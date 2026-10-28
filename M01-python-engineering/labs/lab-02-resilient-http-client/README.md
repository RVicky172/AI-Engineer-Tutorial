# M01 · Lab 02: Resilient HTTP client wrapper

> Module: [Python and Software Engineering Fundamentals](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)
>
> **Reference solution included** (`src/`, `tests/`, `NOTES.md`). Try the lab yourself first for 60-90 minutes, then compare. See [../../LEARNINGS.md](../../LEARNINGS.md) for how to study it.

## Goal
Write a reusable async HTTP client with retries, exponential backoff with jitter, a circuit breaker and per-call timeouts; unit-test every failure path with respx.

## Steps
1. Create `ResilientClient` wrapping one shared `httpx.AsyncClient` (connection pooling).
2. Support per-call `timeout` (connect/read) overriding a default.
3. Retry only retryable failures: connect errors, timeouts, 429, 502/503/504. Never retry 4xx validation errors.
4. Backoff: `sleep = random.uniform(0, min(cap, base * 2**attempt))` (full jitter). Honour `Retry-After` on 429.
5. Send an `Idempotency-Key` header on POSTs so retries are safe for servers that support it.
6. Circuit breaker: CLOSED -> OPEN after N consecutive failures; OPEN rejects fast for `reset_timeout`; then HALF_OPEN allows one probe.
7. Inject the sleep function and clock so tests run instantly.
8. respx tests: 2x 503 then 200; 429 with Retry-After; 400 not retried; timeout; breaker opens and half-opens.

## Done when
- [ ] All failure-path tests pass in < 2 seconds
- [ ] Logs show attempt number, delay and reason for each retry
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Add a token-bucket rate limiter (e.g. 10 req/s) shared across concurrent coroutines.

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
