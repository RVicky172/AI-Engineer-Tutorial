# M01 · Python and Software Engineering Fundamentals — Study Guide

> **Priority:** Must have · **Week:** 1 · **Study time:** ~3 h · **Labs:** [../labs](../labs/SETUP.md)

## Why it matters
Python is where agent logic, tool integrations and glue code live. In this role you write **production services**, not notebooks: async, typed, tested, observable, and resilient to flaky LLMs and enterprise APIs.

## Learning objectives
By the end you can:
- Write async Python that never blocks the event loop and calls many APIs concurrently.
- Model and validate data with type hints, dataclasses and Pydantic v2.
- Build a FastAPI service with dependency injection, streaming (SSE), middleware and clean error handling.
- Make outbound calls safe: timeouts, retries with backoff + jitter, idempotency, circuit breaking, rate limiting.
- Test it all with pytest, fixtures and mocks (respx for HTTP, moto for AWS), and keep it clean with ruff + mypy.

---

## 1. Async Python
An `async def` function returns a coroutine; `await` yields control to the **event loop** while waiting on I/O. One thread can then serve thousands of concurrent requests — but only if nothing blocks.

```python
import asyncio, httpx

async def fetch_all(urls: list[str]) -> list[int]:
    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=3.0)) as client:
        responses = await asyncio.gather(*(client.get(u) for u in urls), return_exceptions=True)
    return [r.status_code if isinstance(r, httpx.Response) else -1 for r in responses]
```

Key ideas:
- **Blocking calls freeze everything.** `time.sleep`, `requests.get`, sync `boto3` calls, CPU-heavy parsing inside an `async def` stop *all* other requests. Offload with `await asyncio.to_thread(fn, ...)` or use async libraries.
- **Bound concurrency** with `asyncio.Semaphore(n)` so a fan-out doesn't overload a downstream API.
- **Timeouts everywhere:** `asyncio.timeout(5)` (3.11+) or client-level timeouts. A missing timeout is the most common cause of hung agents.
- **Structured concurrency:** `asyncio.TaskGroup` (3.11+) cancels sibling tasks if one fails.
- **Reuse clients:** create one `httpx.AsyncClient` per app (connection pooling), close it on shutdown.

## 2. Types, dataclasses and Pydantic v2
- **Type hints** + `mypy` catch bugs before runtime and document intent.
- **`@dataclass`** for internal plain data with no validation needs.
- **Pydantic `BaseModel`** at boundaries (HTTP input, LLM output, config) where data is untrusted.

```python
from pydantic import BaseModel, Field, field_validator
from typing import Literal
from uuid import UUID

class Ticket(BaseModel):
    id: str = Field(pattern=r"^INC\d{7}$")
    severity: Literal["P1", "P2", "P3", "P4"]
    summary: str = Field(min_length=5, max_length=300)
    session_id: UUID

    @field_validator("summary")
    @classmethod
    def strip(cls, v: str) -> str:
        return v.strip()

Ticket.model_validate_json(raw_json)   # parse + validate
Ticket.model_json_schema()             # JSON schema → reuse as an LLM tool/output schema
```
The same model can validate API input **and** define the JSON schema you send to the LLM — one source of truth.

## 3. FastAPI essentials
- **Dependency injection** (`Depends`) for settings, clients, auth, DB sessions — easy to override in tests (`app.dependency_overrides`).
- **Lifespan** to create/close shared clients.
- **Streaming:** LLM tokens are streamed with Server-Sent Events (`text/event-stream`): each message is `data: ...\n\n`.
- **Middleware** for request IDs, timing and logging.
- **Exception handlers** to return one consistent error shape.
- **Background tasks** for fire-and-forget work (for anything important, use a queue: SQS).

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from sse_starlette.sse import EventSourceResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http = httpx.AsyncClient()
    yield
    await app.state.http.aclose()

app = FastAPI(lifespan=lifespan)

@app.post("/chat")
async def chat(req: ChatRequest, request: Request):
    async def events():
        async for token in generate(req.message):
            if await request.is_disconnected():
                break
            yield {"event": "token", "data": token}
        yield {"event": "done", "data": ""}
    return EventSourceResponse(events())
```

## 4. Tooling
| Tool | Purpose |
|---|---|
| `uv` | fast env + dependency manager (`uv init`, `uv add`, `uv run`, lockfile) |
| `ruff` | lint + format (replaces flake8/isort/black) |
| `mypy` | static type checking |
| `pytest`, `pytest-asyncio` | tests, async tests |
| `pytest-cov` | coverage with `--cov-fail-under` gate |
| `respx` | mock `httpx` calls |
| `moto` | in-memory fake AWS (`@mock_aws`) |

Testing patterns: **fixtures** for setup, **parametrize** for tables of cases, **dependency overrides** in FastAPI, and test **failure paths** more than happy paths.

## 5. Resilience for LLM and enterprise calls
| Technique | What it does | Notes |
|---|---|---|
| Timeout | caps time per call | set connect + read timeouts; also an overall budget for the agent run |
| Retry | repeats transient failures | only on timeouts, connection errors, 429, 502/503/504 — never on 400/401/403/404 |
| Exponential backoff + jitter | spreads retries | `sleep = random.uniform(0, min(cap, base * 2**attempt))`; honour `Retry-After` |
| Idempotency | makes retries safe | idempotency key per logical operation; server de-duplicates |
| Circuit breaker | stops hammering a dead dependency | closed → open after N failures → half-open probe |
| Rate limiter | stays under upstream limits | token bucket shared across coroutines |

**Idempotency for agent tools:** the agent (or your retry layer) may call `restart_service` twice. Generate a key from the logical action (e.g. `hash(session_id, tool, args)`), pass it to the API, or keep a short-lived "already done" record and return the original result.

## 6. Logging and configuration
- **Structured JSON logs** (structlog / python-json-logger) with `request_id`, `session_id`, `trace_id` on every line — searchable in CloudWatch Logs Insights.
- **Never log** secrets, tokens, full prompts with PII. Log sizes, IDs and hashes instead.
- **Config** from env vars via `pydantic-settings`; secrets from Secrets Manager at runtime, cached with a TTL. No secrets in code, images or git.

## Common pitfalls
- Sync `boto3` inside async handlers without `to_thread` → latency spikes under load.
- Creating a new HTTP client per request → socket exhaustion, slow TLS handshakes.
- Retrying non-idempotent POSTs without a key → duplicate tickets/restarts.
- Retry storms: every layer retrying 3x → 27 calls. Retry at **one** layer.
- Tests that hit real AWS/LLMs → slow, flaky, costly. Mock at the boundary.

---

## Self-check (try first, then open)
<details><summary>How do you make an LLM tool call idempotent when the agent retries?</summary>

Derive an idempotency key from the logical operation (session + tool + normalised args, or an operation ID the agent is given), send it to the downstream API if it supports idempotency keys, otherwise store `key → result` (e.g. DynamoDB with TTL, conditional put) and return the stored result on repeat. Make read tools naturally idempotent; design write tools as "set state to X" rather than "toggle". Add approval for destructive actions so a retry can't silently repeat them.
</details>

<details><summary>What happens to an asyncio service if one downstream call blocks the event loop?</summary>

The whole process stops serving: every other request, health check and stream stalls until the blocking call returns. Symptoms: latency spikes for unrelated requests, health-check failures, container restarts. Fix: use async clients, `asyncio.to_thread` for sync SDKs/CPU work, timeouts, and detect with asyncio debug mode / slow-callback warnings.
</details>

## Resources
- Python docs: *asyncio* (Tasks, TaskGroup, timeouts)
- FastAPI docs: Dependencies, Lifespan Events, Testing
- Pydantic v2 docs: Models, Validators, JSON Schema
- AWS Builders' Library: *Timeouts, retries and backoff with jitter*; *Making retries safe with idempotent APIs*
- uv, ruff, mypy, respx, moto documentation

**Next:** [Lab environment setup](../labs/SETUP.md) → [Lab 01](../labs/lab-01-fastapi-sse-chat/README.md)
