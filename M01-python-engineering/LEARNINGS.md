# M01 Learnings — what the labs taught, and what to do better

The three labs are built, tested and green (`labs/check.sh`). This page collects the lessons that apply **beyond** each lab, the mistakes made along the way, and improvements to how you study. Read each lab's `NOTES.md` for the details.

| Lab | Result | Most important lesson |
|---|---|---|
| [01 FastAPI SSE chat](labs/lab-01-fastapi-sse-chat/NOTES.md) | 19 tests · 97% coverage | After the first streamed byte you can't change the status code, so errors go *inside* the stream |
| [02 Resilient HTTP client](labs/lab-02-resilient-http-client/NOTES.md) | 28 tests · 100% coverage | Retries are only safe with idempotency; every exit from a breaker probe must release it |
| [03 moto AWS testing](labs/lab-03-moto-aws-testing/NOTES.md) | 12 tests · 100% coverage | Secrets leak through exception chains, and `from None` doesn't stop it |

---

## 1. Habits that showed their value (keep doing them)

1. **Test failure paths first.** Every bug found in this module came from a failure-path test or from reviewing failure handling. None came from happy-path tests.
2. **Assert on everything the client sees:** headers, error body shape, log lines, what's *absent* (no leaked secret). The duplicate `X-Request-ID` bug was invisible to status-code checks.
3. **Mutation-check important tests.** Remove the fix, run the test, and watch it fail. This was done for the breaker and secret-leak tests, and it proved one of my own explanations wrong.
4. **Inject time, randomness and clients.** `sleep`, `clock`, `rand` and boto3 clients are parameters, so tests are deterministic, fast (59 tests in ~6 s) and never touch the network.
5. **Verify on the real thing once.** In-process test clients buffer responses. Only a real `uvicorn` + `curl -N` run proved tokens actually stream about 50 ms apart.
6. **Let the tools argue with you.** ruff and mypy `--strict` flagged five real design questions (B008, ASYNC109, a property that mypy narrowed wrongly, asserts used for typing, missing boto3 types). For each one, understand it first, then fix it or suppress it **with a comment explaining why**.

## 2. Mistakes made while building (learn from these)

| Mistake | Why it's tempting | Better approach |
|---|---|---|
| `headers.append()` in middleware | "add a header" sounds like append | Headers that must appear once: **set** them |
| Half-open breaker never released on 429 / cancellation | You think of success and failure, not "neither" | List *every* exit path of a state machine: success, failure, cancel, unexpected exception |
| `raise ... from None` to "hide" a secret | The traceback looks clean | `__context__` still holds it. Raise outside the `except` block, and test the chain |
| `assert isinstance(...)` in production code to satisfy mypy | Quick way to narrow a type | `python -O` strips asserts. Restructure so the types are right (typed handler registration) |
| Expecting `httpx.ASGITransport` to run lifespan and stream | It feels like a real server | It doesn't run lifespan and it buffers. Know your test tool's limits |
| Scripted edits leaving code unformatted | Quick regex edits | `check.sh` caught it. Always run the full gate before you call something done |

## 3. How these labs connect to the rest of the course

- `ChatModel` Protocol (Lab 01) → implement `BedrockChatModel` with `converse_stream` in **M05**.
- `ResilientClient` (Lab 02) → put it under the ServiceNow/MCP tools in **M07**, and map its errors to model-friendly tool errors (M07 Lab 04).
- `ConfigLoader` (Lab 03) → load secrets in the chat service lifespan, and write its least-privilege IAM policy in **M08**.
- Request IDs + JSON logs (Lab 01) → become OpenTelemetry trace IDs in **M10**.
- The test style (fakes, failure paths, gates) → scales into scenario evals in **M11**.

## 4. Improvements to how you study this module

1. **Attempt each lab yourself first.** Give it 60-90 minutes from the lab README *without* opening `src/`. Then diff your version against the reference and write down 3 differences in `docs/notes.md`. Reading working code feels like learning; writing it is learning.
2. **Re-type, don't copy.** If you use the reference, type it by hand into a scratch folder. You'll notice details (`raise` after `CancelledError`, `include_input=False`) that skimming misses.
3. **Break things on purpose.** For each lab, delete one safety line (the `raise` in the `CancelledError` handler, `abandon_probe()`, the `no_real_aws` fixture) and predict which test fails *before* running it.
4. **Do the "Improve it yourself" lists.** They're ordered by value. The rate limiter (Lab 02 #1) and single-flight secret refresh (Lab 03 #2) come back in M07.
5. **Answer the self-check questions aloud** (in `../README.md`). Both M01 questions are answered by these labs:
   - *Idempotent tool calls when the agent retries?* → Lab 02, learning #4
   - *What happens if one call blocks the event loop?* → Lab 01's `asyncio.sleep` comment + Lab 03 "Improve it" #1. Try it: put `time.sleep(2)` in `FakeChatModel` and stream two requests at once.

## 5. Changes made to the lab setup
- `labs/SETUP.md`: added the plain-`pip` route (uv is optional) and the Intel Mac `cryptography` wheel fix.
- `labs/requirements.txt`: added `boto3-stubs[s3,secretsmanager]` so mypy can check boto3 code.
- `labs/check.sh`: one command runs tests + coverage, ruff, format and mypy for all labs.
- Each lab has its own `pyproject.toml` with pytest, ruff (incl. security rules `S` and async rules `ASYNC`) and mypy `--strict` settings. Copy this setup into later modules.
