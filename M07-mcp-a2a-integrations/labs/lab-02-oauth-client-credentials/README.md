# M07 · Lab 02: OAuth 2.0 client credentials with caching and refresh

> Module: [MCP, A2A and Enterprise Integrations](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)

## Goal
Implement OAuth 2.0 client-credentials against a mock provider, with token caching and refresh, inside a tool.

## Steps
1. Build a mock token endpoint (FastAPI) that issues short-lived JWTs (e.g. 60s) and a protected API that validates them.
2. Write `TokenProvider`: caches the token, refreshes when < 10s from expiry, uses an `asyncio.Lock` so concurrent calls fetch only once.
3. On a 401 from the API, invalidate the cache and retry exactly once.
4. Load client secret from env/Secrets Manager, never log it.
5. Tests: cache hit, refresh on expiry, single fetch under 20 concurrent calls, 401 retry.

## Done when
- [ ] All tests pass; logs show token fetch count
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Implement authorization code + PKCE for a user-delegated flow.

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
