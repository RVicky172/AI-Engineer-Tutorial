# M01 · Lab 01: FastAPI chat service with SSE streaming

> Module: [Python and Software Engineering Fundamentals](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)

## Goal
Build a FastAPI service with a `/chat` endpoint that streams tokens via Server-Sent Events, validates input with Pydantic, and has 80%+ test coverage.

## Steps
1. Scaffold with `uv init --package chat-service` and use a `src/` layout.
2. Define a `ChatRequest` Pydantic model (`message`: 1-4000 chars, `session_id`: UUID) and a `ChatChunk` response model.
3. Add `GET /health` and `POST /chat`. For now, stream from a fake async generator that yields words with `await asyncio.sleep(0.05)` (you will swap in Bedrock in M05).
4. Return the stream with `EventSourceResponse` (sse-starlette) and send a final `event: done`.
5. Add middleware that sets/propagates an `X-Request-ID` header and binds it to JSON logs (structlog).
6. Add a global exception handler that returns `{"error": {"code", "message", "request_id"}}`.
7. Load config with `pydantic-settings` from env vars; no hard-coded secrets.
8. Test with `httpx.AsyncClient(transport=ASGITransport(app=app))`: happy path, validation error (422), stream content, request-ID echo.
9. Run `pytest --cov=chat_service --cov-fail-under=80`, `ruff check .`, `mypy src`.

## Done when
- [ ] `curl -N -X POST localhost:8000/chat -H 'content-type: application/json' -d '{...}'` shows tokens arriving one by one
- [ ] Invalid input returns 422 with a clear message
- [ ] Coverage gate passes; ruff and mypy are clean
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Handle client disconnects mid-stream (check `await request.is_disconnected()`) and cancel upstream work.

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
