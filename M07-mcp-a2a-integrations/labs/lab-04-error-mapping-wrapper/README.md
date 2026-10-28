# M07 · Lab 04: Map messy API errors into actionable tool errors

> Module: [MCP, A2A and Enterprise Integrations](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)

## Goal
Write a tool wrapper that converts e.g. a 500 with an HTML body into a short, actionable message for the model.

## Steps
1. Define `ToolError(code, message, retryable, hint)`.
2. Map: timeout, connection error, 400, 401/403, 404, 409, 429 (with Retry-After), 5xx with HTML body.
3. Strip HTML, truncate to ~300 chars, never include secrets or stack traces.
4. Add a hint the model can act on ('ticket not found: check the number format INC0012345').
5. Tests with respx for every mapping.

## Done when
- [ ] Every mapping tested
- [ ] Before/after example of what the model sees
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Add a shared rate limiter (10 req/s) so parallel tool calls never exceed the upstream limit.

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
