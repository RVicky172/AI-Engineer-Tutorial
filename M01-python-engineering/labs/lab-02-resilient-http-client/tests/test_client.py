import asyncio
from collections.abc import Callable

import httpx
import pytest
import respx

from resilient_http import (
    BreakerState,
    CircuitBreaker,
    CircuitOpenError,
    ResilientClient,
    RetriesExhaustedError,
    RetryPolicy,
)
from tests.conftest import BASE, FakeTime

URL = f"{BASE}/tickets"


def state_of(breaker: CircuitBreaker) -> BreakerState:
    # mypy assumes a property returns the same value on every read and "narrows" it after an
    # assert. Our state changes as time passes, so read it through a function instead.
    return breaker.state


@respx.mock
async def test_retries_transient_errors_then_succeeds(
    client: ResilientClient, fake_time: FakeTime
) -> None:
    route = respx.get(URL).mock(
        side_effect=[httpx.Response(503), httpx.Response(502), httpx.Response(200, json=[])]
    )

    response = await client.get("/tickets")

    assert response.status_code == 200
    assert route.call_count == 3
    assert fake_time.sleeps == [0.2, 0.4]  # base * 2**attempt (rand fixed to the maximum)


@respx.mock
async def test_does_not_retry_client_errors(client: ResilientClient, fake_time: FakeTime) -> None:
    route = respx.get(URL).mock(return_value=httpx.Response(400, json={"error": "bad query"}))

    response = await client.get("/tickets")

    assert response.status_code == 400  # returned as-is: retrying a bad request can't fix it
    assert route.call_count == 1
    assert fake_time.sleeps == []


@respx.mock
async def test_honours_retry_after_on_429(client: ResilientClient, fake_time: FakeTime) -> None:
    respx.get(URL).mock(
        side_effect=[httpx.Response(429, headers={"Retry-After": "3"}), httpx.Response(200)]
    )

    response = await client.get("/tickets")

    assert response.status_code == 200
    assert fake_time.sleeps == [3.0]  # exactly what the server asked, no jitter


@respx.mock
async def test_gives_up_when_retry_after_is_too_long(client: ResilientClient) -> None:
    route = respx.get(URL).mock(return_value=httpx.Response(429, headers={"Retry-After": "3600"}))

    with pytest.raises(RetriesExhaustedError, match="wait 3600s") as err:
        await client.get("/tickets")

    assert route.call_count == 1
    assert err.value.last_response is not None
    assert err.value.last_response.status_code == 429


@respx.mock
async def test_timeouts_exhaust_retries_and_keep_the_cause(client: ResilientClient) -> None:
    route = respx.get(URL).mock(side_effect=httpx.ReadTimeout("slow upstream"))

    with pytest.raises(RetriesExhaustedError) as err:
        await client.get("/tickets")

    assert route.call_count == 4
    assert err.value.attempts == 4
    assert isinstance(err.value.last_exception, httpx.ReadTimeout)


@respx.mock
async def test_stops_when_time_budget_would_be_exceeded(
    make_client: Callable[..., ResilientClient], fake_time: FakeTime
) -> None:
    policy = RetryPolicy(max_attempts=10, backoff_base=1.0, total_timeout=5.0)
    route = respx.get(URL).mock(return_value=httpx.Response(503))

    async with make_client(policy=policy) as client:
        with pytest.raises(RetriesExhaustedError, match="time budget"):
            await client.get("/tickets")

    assert fake_time.sleeps == [1.0, 2.0]  # next sleep (4s) would pass the 5s budget
    assert route.call_count == 3


@respx.mock
async def test_per_call_timeout_is_passed_to_httpx(client: ResilientClient) -> None:
    route = respx.get(URL).mock(return_value=httpx.Response(200))

    await client.get("/tickets", timeout=1.5)

    timeouts = route.calls.last.request.extensions["timeout"]
    assert timeouts["read"] == 1.5


# --- non-idempotent requests ---------------------------------------------------------------


@respx.mock
async def test_post_without_idempotency_key_is_not_retried_on_5xx(client: ResilientClient) -> None:
    route = respx.post(URL).mock(return_value=httpx.Response(503))

    response = await client.post("/tickets", json={"title": "disk full"})

    # The server may have created the ticket before failing; retrying could duplicate it.
    assert response.status_code == 503
    assert route.call_count == 1


@respx.mock
async def test_post_without_key_is_not_retried_after_read_timeout(client: ResilientClient) -> None:
    route = respx.post(URL).mock(side_effect=httpx.ReadTimeout("no answer"))

    with pytest.raises(httpx.ReadTimeout):
        await client.post("/tickets", json={"title": "disk full"})

    assert route.call_count == 1


@respx.mock
async def test_post_without_key_is_retried_when_it_never_reached_the_server(
    client: ResilientClient,
) -> None:
    route = respx.post(URL).mock(
        side_effect=[httpx.ConnectError("refused"), httpx.Response(201, json={"id": 1})]
    )

    response = await client.post("/tickets", json={"title": "disk full"})

    assert response.status_code == 201
    assert route.call_count == 2


@respx.mock
async def test_post_with_idempotency_key_is_retried_with_the_same_key(
    client: ResilientClient,
) -> None:
    route = respx.post(URL).mock(side_effect=[httpx.Response(503), httpx.Response(201)])

    response = await client.post("/tickets", json={"title": "x"}, idempotency_key="op-42")

    assert response.status_code == 201
    keys = [call.request.headers["Idempotency-Key"] for call in route.calls]
    assert keys == ["op-42", "op-42"]  # same key on every attempt = server can de-duplicate


# --- circuit breaker -----------------------------------------------------------------------


@respx.mock
async def test_breaker_opens_and_then_fails_fast_without_calling(
    make_client: Callable[..., ResilientClient], fake_time: FakeTime
) -> None:
    breaker = CircuitBreaker(failure_threshold=3, reset_timeout=30, clock=fake_time.clock)
    route = respx.get(URL).mock(return_value=httpx.Response(503))

    async with make_client(breaker=breaker) as client:
        with pytest.raises(CircuitOpenError):  # 3 failures open it during the 4th attempt
            await client.get("/tickets")
        assert state_of(breaker) is BreakerState.OPEN
        calls_so_far = route.call_count

        with pytest.raises(CircuitOpenError):
            await client.get("/tickets")
        assert route.call_count == calls_so_far  # failed fast: no request was sent


@respx.mock
async def test_breaker_half_open_probe_success_closes_it(
    make_client: Callable[..., ResilientClient], fake_time: FakeTime
) -> None:
    breaker = CircuitBreaker(failure_threshold=1, reset_timeout=30, clock=fake_time.clock)
    respx.get(URL).mock(side_effect=[httpx.Response(503), httpx.Response(200)])

    async with make_client(policy=RetryPolicy(max_attempts=1), breaker=breaker) as client:
        with pytest.raises(RetriesExhaustedError):
            await client.get("/tickets")
        assert state_of(breaker) is BreakerState.OPEN

        fake_time.advance(30)
        assert state_of(breaker) is BreakerState.HALF_OPEN
        assert (await client.get("/tickets")).status_code == 200
        assert state_of(breaker) is BreakerState.CLOSED


def test_breaker_half_open_probe_failure_reopens_it(fake_time: FakeTime) -> None:
    breaker = CircuitBreaker(failure_threshold=1, reset_timeout=30, clock=fake_time.clock)
    breaker.record_failure()
    fake_time.advance(30)

    breaker.before_call()  # the probe
    with pytest.raises(CircuitOpenError):
        breaker.before_call()  # a second caller must wait for the probe's verdict
    breaker.record_failure()

    assert state_of(breaker) is BreakerState.OPEN


@respx.mock
async def test_breaker_is_not_stuck_when_probe_gets_429(
    make_client: Callable[..., ResilientClient], fake_time: FakeTime
) -> None:
    breaker = CircuitBreaker(failure_threshold=1, reset_timeout=30, clock=fake_time.clock)
    breaker.record_failure()
    fake_time.advance(30)
    respx.get(URL).mock(return_value=httpx.Response(429, headers={"Retry-After": "1"}))

    async with make_client(policy=RetryPolicy(max_attempts=1), breaker=breaker) as client:
        with pytest.raises(RetriesExhaustedError):
            await client.get("/tickets")

    assert state_of(breaker) is BreakerState.CLOSED  # server answered, so it is alive


async def test_breaker_is_not_stuck_when_probe_is_cancelled(
    make_client: Callable[..., ResilientClient], fake_time: FakeTime
) -> None:
    breaker = CircuitBreaker(failure_threshold=1, reset_timeout=30, clock=fake_time.clock)
    breaker.record_failure()
    fake_time.advance(30)
    started = asyncio.Event()

    async def hang(request: httpx.Request) -> httpx.Response:
        started.set()
        await asyncio.Event().wait()
        raise AssertionError("unreachable")

    with respx.mock:
        respx.get(URL).mock(side_effect=hang)
        async with make_client(breaker=breaker) as client:
            task = asyncio.create_task(client.get("/tickets"))
            await started.wait()
            task.cancel()  # e.g. the agent's turn timed out
            with pytest.raises(asyncio.CancelledError):
                await task

    breaker.before_call()  # would raise CircuitOpenError if the probe slot leaked


@respx.mock
async def test_client_errors_do_not_trip_the_breaker(
    make_client: Callable[..., ResilientClient], fake_time: FakeTime
) -> None:
    breaker = CircuitBreaker(failure_threshold=2, clock=fake_time.clock)
    respx.get(URL).mock(return_value=httpx.Response(404))

    async with make_client(breaker=breaker) as client:
        for _ in range(5):
            await client.get("/tickets")

    assert state_of(breaker) is BreakerState.CLOSED  # 404s are our bug, not the dependency's
