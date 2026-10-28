from collections.abc import AsyncIterator, Callable

import pytest

from resilient_http import CircuitBreaker, ResilientClient, RetryPolicy

BASE = "https://api.example.test"


class FakeTime:
    """A clock that only moves when the code under test 'sleeps'. Tests run in ~0 seconds
    and we can assert exactly how long the client *would* have waited."""

    def __init__(self) -> None:
        self.now = 1000.0
        self.sleeps: list[float] = []

    def clock(self) -> float:
        return self.now

    async def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture
def fake_time() -> FakeTime:
    return FakeTime()


@pytest.fixture
def make_client(fake_time: FakeTime) -> Callable[..., ResilientClient]:
    def factory(
        policy: RetryPolicy | None = None, breaker: CircuitBreaker | None = None
    ) -> ResilientClient:
        return ResilientClient(
            BASE,
            policy=policy or RetryPolicy(max_attempts=4, backoff_base=0.2, backoff_cap=10.0),
            breaker=breaker or CircuitBreaker(failure_threshold=100, clock=fake_time.clock),
            sleep=fake_time.sleep,
            clock=fake_time.clock,
            rand=lambda low, high: high,  # deterministic: always the maximum jittered delay
        )

    return factory


@pytest.fixture
async def client(make_client: Callable[..., ResilientClient]) -> AsyncIterator[ResilientClient]:
    async with make_client() as c:
        yield c
