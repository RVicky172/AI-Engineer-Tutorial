# M11 · Lab 03: Load test with 50 concurrent users

> Module: [Testing and Evaluation of Agentic Systems](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)

## Goal
Load-test your service with 50 concurrent users and record where throttling or latency starts to degrade.

## Steps
1. Locust file hitting `/chat` (streaming) with realistic prompts; measure time to first byte and total time.
2. Ramp 1 -> 50 users; watch p50/p95, errors, Bedrock throttles.
3. Find the knee point and the first failing dependency.
4. Add backpressure (concurrency semaphore / queue / 429 with Retry-After) and retest.

## Done when
- [ ] Graph or table of latency vs users, before/after backpressure
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Chaos test: kill a dependency mid-test and verify graceful degradation.

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
