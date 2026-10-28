# Lab 02 Notes — Resilient HTTP client wrapper

## What I built
`ResilientClient`: an async wrapper around **one shared** `httpx.AsyncClient` that adds per-call timeouts, an overall time budget, retries with exponential backoff and full jitter, `Retry-After` support, idempotency-aware retry rules, and a circuit breaker. This is the client you will put inside agent tools (M04, M07) that call ticketing, monitoring and CMDB APIs.

```
src/resilient_http/
├── client.py    ResilientClient + RetryPolicy: the retry loop and its rules
├── breaker.py   CircuitBreaker: CLOSED -> OPEN -> HALF_OPEN state machine
├── backoff.py   full_jitter(), parse_retry_after(): pure functions, easy to test
└── errors.py    CircuitOpenError, RetriesExhaustedError (carry the last response/exception)
tests/           28 tests, 100% coverage, run in < 1 s (fake clock: nothing really sleeps)
```

## Commands
```bash
cd M01-python-engineering/labs && source .venv/bin/activate && cd lab-02-resilient-http-client
pytest && ruff check . && ruff format --check . && mypy src tests
```

Usage:
```python
async with ResilientClient(
    "https://dev123.service-now.com", policy=RetryPolicy(max_attempts=4)
) as api:
    r = await api.get("/api/now/table/incident", params={"sysparm_limit": 5}, timeout=5)
    r = await api.post(
        "/api/now/table/incident", json=body, idempotency_key=f"triage-{session_id}-create"
    )
```

## Decision table: what happens on each outcome
| Outcome | GET / PUT / DELETE | POST without key | POST with `idempotency_key` | Breaker |
|---|---|---|---|---|
| 2xx / 3xx | return | return | return | success |
| 400 / 401 / 403 / 404 / 409 | return (no retry) | return | return | success (it's *our* bug) |
| 429 | retry, honour `Retry-After` | retry (429 = not processed) | retry | success (server is alive) |
| 502 / 503 / 504 | retry with jitter | **return, no retry** (may have been processed) | retry | failure |
| `ConnectError` / `ConnectTimeout` | retry | retry (never reached the server) | retry | failure |
| `ReadTimeout` / other transport error | retry | **raise, no retry** | retry | failure |
| `Retry-After` > 30 s | `RetriesExhaustedError` | same | same | — |
| next sleep would pass `total_timeout` | `RetriesExhaustedError` | same | same | — |
| breaker OPEN | `CircuitOpenError`, **no request sent** | same | same | — |

---

## Key learnings

### 1. Only retry what can succeed next time
Retrying a `400` can never fix it; it only adds load and latency. Retry **transient** failures only: connection problems, timeouts, `429`, `502/503/504`. `500` is deliberately *not* in the retryable set, because it usually means a bug on the server, so the same request fails again.

### 2. Backoff with full jitter
`delay = uniform(0, min(cap, base * 2**attempt))`
- Exponential: gives the dependency more breathing room each time.
- Cap: never wait absurdly long.
- **Jitter:** if 1,000 agent sessions all fail at 12:00:00 and all retry after exactly 0.2 s, they hit the recovering service as one wave (the "thundering herd"). Randomising the delay spreads them out. The test asserts the delays are actually spread, not just within bounds.

### 3. `Retry-After` beats your own guess, but with a limit
When the server says how long to wait, use exactly that (no jitter). But an agent turn can't block for an hour, so above `max_retry_after` we fail fast with a clear error, and the caller (or the model) can decide what to do.

### 4. Idempotency is what makes retries safe
A `POST /tickets` that times out *may have created the ticket*. Retrying blindly creates a duplicate; for `restart_service` that would be a second restart. Rules:
- `GET/PUT/DELETE` are idempotent by HTTP semantics, so it's safe to repeat them.
- `POST` is retried only with an `Idempotency-Key`, which must be the **same on every attempt** (the test checks this) and must identify the *logical operation* (e.g. `f"{session_id}:{tool}:{hash(args)}"`), not a random value per attempt.
- Exception: a `ConnectError` means the request never left, so even a keyless POST is safe to retry.

This is the answer to the M01 self-check question *"How do you make an LLM tool call idempotent when the agent retries?"*

### 5. Circuit breaker: fail fast and protect the dependency
After N consecutive failures the breaker **opens**: calls fail instantly without touching the network, which saves your latency budget and gives the dependency time to recover. After `reset_timeout` it goes **half-open** and lets exactly **one probe** through. If the probe succeeds the breaker closes; if it fails, the breaker reopens.
What counts as a failure is a design decision. Here, 5xx and transport errors count; 4xx and 429 don't, because the server answered and is alive.

### 6. Time budgets beat attempt counts
`max_attempts=4` with growing sleeps could take 20+ seconds. Agents have a **time budget** per turn, so `total_timeout` stops retrying when the next sleep would overrun the budget.

### 7. Inject time to make resilience code testable
`sleep`, `clock` and `rand` are constructor arguments. Tests pass a `FakeTime` whose clock only moves when the code "sleeps". 28 tests covering minutes of simulated backoff run in under a second, and they assert exact delays (`[0.2, 0.4]`) instead of "roughly".

### 8. One shared `httpx.AsyncClient`
Creating a client per request means a new TCP and TLS handshake every time, and under load it exhausts sockets. One client per service per process gives you connection pooling. Close it with `async with` / `aclose()`.

---

## Bugs found while building this

| Bug | How it was found | Fix / lesson |
|---|---|---|
| Breaker stuck **half-open forever** when the probe got a `429` | Re-reading the state machine: a 429 recorded neither success nor failure, so the probe slot was never freed | 429 counts as "alive" (`record_success`). **Every path out of a probe must release it.** |
| Breaker stuck half-open when the probe call was **cancelled** | Same review. `CancelledError` is a `BaseException`, so it skipped the `except` blocks | `except BaseException: breaker.abandon_probe(); raise`. Agents cancel tool calls all the time (turn timeouts), so this would have hit production. |
| Proving the two tests are real | Mutation check: removed each fix from a copy of the code and ran the tests | Both tests failed without the fix and passed with it. **A regression test that can't fail is worthless.** Try this habit on your own tests. |
| mypy: "non-overlapping identity check" | mypy assumes a property returns the same value on every read, but `breaker.state` changes as the clock moves | Read it through a function (`state_of(breaker)`). Know *why* the type checker complains before silencing it. |
| ruff `B008` | `httpx.Timeout(...)` in a default argument is evaluated once at import time | Module-level `DEFAULT_TIMEOUT` constant (same behaviour, made explicit) |
| ruff `ASYNC109` | An async function with a `timeout` parameter usually should use `asyncio.timeout` instead | Kept on purpose: it mirrors httpx's per-request timeout API. Suppressed with a `noqa` **and a comment saying why**. Never suppress silently. |

---

## Improve it yourself
1. **Rate limiter (the lab's stretch):** add an async token bucket (10 req/s, burst 5) shared by all coroutines using the client. Test it with the fake clock: 20 concurrent calls must take about 1.5 s of simulated time. This answers the M07 self-check about fan-out.
2. **Retry metrics:** count retries and breaker opens per host (structlog fields now, CloudWatch EMF metrics in M10). How would you alert on "breaker opened"?
3. **Breaker per host:** one `ResilientClient` might call several hosts. Should one failing host open the breaker for all of them? Make breakers keyed by host.
4. **Retry budget across the fleet:** if *every* layer retries 3 times (agent → tool → client → SDK), one failure becomes 27 calls. Find where Bedrock's boto3 client already retries (M05) and decide which layer owns retries.
5. **Use it for real:** in M07 Lab 04, put this client under your ServiceNow tools and map `RetriesExhaustedError` / `CircuitOpenError` into model-friendly tool errors.

## What I'd explain in an interview
- "I retry only transient failures, with exponential backoff and full jitter to avoid thundering herds, and I honour `Retry-After` up to a cap."
- "Non-idempotent calls are retried only with an idempotency key tied to the logical operation; a connect error is the one case that's always safe."
- "A circuit breaker fails fast when a dependency is down. The subtle part is making sure every exit path from the half-open probe frees it, including cancellation."
- "I inject the clock and sleep, so failure-path tests are deterministic and run in milliseconds."
