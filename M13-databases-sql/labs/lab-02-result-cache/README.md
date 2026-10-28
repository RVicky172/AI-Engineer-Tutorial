# M13 · Lab 02: Result cache for the SQL tool

> Module: [Databases, SQL and Enterprise Data Sources](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)

## Goal
Add a result cache and measure the effect on latency and cost.

## Steps
1. Cache question -> SQL (normalised question) and SQL -> result (normalised SQL hash), with TTL.
2. Run a 30-question workload with repeats, with and without cache.
3. Measure latency, model tokens, DB time.
4. Write down the invalidation strategy and the staleness the business can accept.

## Done when
- [ ] Before/after numbers and an invalidation note
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Move the cache to ElastiCache/DynamoDB and discuss multi-instance consistency.

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
