# Lab 01 Notes — FastAPI chat service with SSE streaming

## What I built
A FastAPI service with `GET /health` and `POST /chat`. `/chat` validates input with Pydantic and streams a (fake) model's reply token by token as Server-Sent Events. Every response carries an `X-Request-ID`, every log line is JSON with that ID, and every error has the same JSON shape.

```
src/chat_service/
├── main.py        create_app() factory, routes, stream_events() generator
├── models.py      ChatRequest / ChatChunk / ErrorResponse (Pydantic v2)
├── llm.py         ChatModel Protocol + FakeChatModel (swap for Bedrock in M05)
├── middleware.py  pure-ASGI request-ID + access-log middleware
├── errors.py      one error shape for 422 / 404 / 500
├── log.py         structlog JSON configuration
└── config.py      pydantic-settings (env prefix CHAT_)
tests/             19 tests, 97% coverage
```

## Commands
```bash
cd M01-python-engineering/labs && source .venv/bin/activate && cd lab-01-fastapi-sse-chat

pytest                                    # tests + coverage gate (80%)
ruff check . && ruff format --check .     # lint + format
mypy src tests                            # strict type check

# run it (pretty logs for local dev)
CHAT_LOG_JSON=false uvicorn chat_service.main:create_app --factory --app-dir src --reload

# watch tokens arrive one by one (-N = no buffering)
curl -N -X POST localhost:8000/chat -H 'content-type: application/json' \
  -d '{"message":"hello","session_id":"3fa85f64-5717-4562-b3fc-2c963f66afa6"}'
```
Interactive API docs: http://localhost:8000/docs

## Results
- 19 tests pass in ~0.5 s; coverage 97% (gate: 80%). ruff and mypy `--strict` are clean.
- Verified on a real server: events arrive ~50 ms apart (true streaming), and closing the client mid-stream logs `chat.client_disconnected` with the request ID.

---

## Key learnings (read these slowly)

### 1. App factory instead of a module-level `app`
`create_app(settings, chat_model)` builds a fresh app. Tests create one per test with their own settings and fake model, and importing the module has no side effects (no logging setup, no env reads). Uvicorn supports this with `--factory`.

### 2. Depend on an interface, not a class
The route takes a `ChatModel` (a `Protocol`), resolved through `Depends(get_chat_model)`. That gives two wins:
- Tests swap behaviour with `app.dependency_overrides[get_chat_model] = FailsAfterOneToken`.
- In M05 you write a `BedrockChatModel` with the same `stream()` method and nothing else changes.

### 3. Streaming changes how errors work
The status code is sent with the **first byte**. After the first token goes out, the response is already `200`, so an exception can't become a `500` any more. Failures mid-stream must be reported **inside the stream** (`event: error`), and the client must handle that event. This applies to every LLM streaming API, Bedrock's ConverseStream included.

### 4. Client disconnects: cancellation is your friend
sse-starlette watches for the client going away and **cancels** the generator, which raises `asyncio.CancelledError` at the current `await`. We log it and **re-raise**, so the cancellation also stops the upstream model call. That matters because with a real LLM you would otherwise keep paying for tokens nobody reads.
> Rule: never swallow `CancelledError`. Catch it only to clean up or log, then `raise`.

The lab's stretch goal suggested polling `request.is_disconnected()`. That is the approach for a plain `StreamingResponse`; with sse-starlette it's built in. Know both.

### 5. Pure ASGI middleware vs. `@app.middleware("http")`
`@app.middleware("http")` (BaseHTTPMiddleware) is simpler to write but wraps the app in an extra task and sees streaming bodies only indirectly. A pure ASGI middleware wraps `send`, so it sees the real `http.response.start` (status) and the real end of the stream (duration). For cross-cutting concerns such as request IDs, timing and tracing, pure ASGI is the robust choice.

### 6. The 500 path is different from other errors
Starlette routes errors through two layers:
```
ServerErrorMiddleware        ← unhandled exceptions → our _unhandled_error (OUTSIDE our middleware)
  RequestContextMiddleware   ← ours
    ExceptionMiddleware      ← HTTPException, RequestValidationError → handled INSIDE our middleware
      routes
```
So for a 500, our middleware has already finished and cleared the log context. That's why:
- the request ID is also stored on `request.state` (the scope survives),
- `_unhandled_error` adds the `X-Request-ID` header itself and binds `request_id` to its log line explicitly.

### 7. Logging hygiene
- Log `message_chars`, not the message, because user text can contain personal data (see M12).
- Incoming `X-Request-ID` values are validated (`[A-Za-z0-9._-]{1,64}`). A caller could otherwise inject newlines or huge strings into your logs.
- 500 responses never include exception text. The test plants `password=hunter2` in an exception and asserts it doesn't leak.

### 8. Validation details worth remembering
- `extra="forbid"`: a typo like `mesage` returns 422 instead of being silently ignored.
- `str_strip_whitespace=True` + `min_length=1`: `"   "` is rejected.
- `session_id: UUID` rejects garbage at the edge, so the rest of the code can trust it.

---

## Gotchas found while building this

| Problem | Why it happened | Fix / lesson |
|---|---|---|
| `X-Request-ID: id, id` on 422 responses | The error handler set the header **and** the middleware `append`ed it | Use `headers[name] = value` (set) in middleware. **The parametrized test caught it** — this is why you assert on headers, not just status codes. |
| Lifespan doesn't run in tests | `httpx.ASGITransport` does not send lifespan events | Put the fake model on `app.state` in the factory. For real clients created in lifespan, use `asgi-lifespan`'s `LifespanManager` in the test fixture. |
| 500 test raised instead of returning a response | Starlette re-raises after sending the 500 so the server can log it; `ASGITransport` propagates it | `ASGITransport(app=app, raise_app_exceptions=False)` |
| Tests could be affected by a local `.env` | `BaseSettings` reads `.env` automatically | `Settings(_env_file=None, ...)` in the fixture |
| `assert isinstance(...)` in handlers to satisfy mypy | `add_exception_handler` types the handler as taking `Exception` | Register with `app.exception_handler(Type)(handler)` so each handler keeps its precise type. Never rely on `assert` in production code, because `python -O` removes it. |
| `pip install` failed building `cryptography` | No prebuilt wheel of the newest version for this Intel Mac / macOS 13, and no Xcode tools to compile it | `pip install --only-binary=:all: cryptography` picks the newest version that has a wheel |

---

## Improve it yourself (do these, they're where the learning is)
1. **Heartbeats:** sse-starlette sends a `: ping` comment every 15 s by default. Find the setting, and explain why proxies and load balancers (ALB idle timeout is 60 s) make it necessary.
2. **Time to first token (TTFT):** log `ttft_ms` when the first token is sent. This is a key LLM latency metric (M10).
3. **Timeout per stream:** wrap the model loop in `asyncio.timeout(30)` and send an `error` event with code `timeout`. Write the test first.
4. **Lifespan-managed client:** add an `httpx.AsyncClient` created in the lifespan and closed on shutdown. Make the tests still pass using `asgi-lifespan`.
5. **Max concurrent streams:** add an `asyncio.Semaphore(100)` and return `429` with `Retry-After` when it's full. This is backpressure, revisited in M11 load testing.
6. **Swap the model:** in M05, implement `BedrockChatModel.stream()` with `converse_stream` and inject it. Nothing else should change. If something else does have to change, ask yourself why.

## What I'd explain in an interview
- "Errors after the first streamed byte can't change the status code, so I emit an error event and the client handles it."
- "On client disconnect the generator is cancelled; I re-raise `CancelledError` so the upstream LLM call stops and we stop paying for tokens."
- "Every log line has a request ID bound through contextvars, and 500s still return it in the body and header so support can find the trace."
- "I test failure paths more than happy paths: invalid input, mid-stream failure, disconnect, unhandled exception, and log content."
