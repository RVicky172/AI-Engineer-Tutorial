# M01 · Python and Software Engineering Fundamentals

**Priority:** Must have · **Roadmap week:** 1

Python is the main language for agent logic, integrations and glue code. You are expected to write clean, tested, production-grade code, not notebooks.

## How to work through this module
1. **Study** — read [docs/guide.md](docs/guide.md) and write key points in your own words in [docs/notes.md](docs/notes.md).
2. **Set up** — follow [labs/SETUP.md](labs/SETUP.md).
3. **Practise** — do the labs in order (at least the first two before moving on).
4. **Check** — answer the self-check questions out loud without notes, then update [PROGRESS.md](../PROGRESS.md).

## Labs
Reference solutions are built and tested. Read [LEARNINGS.md](LEARNINGS.md) after the labs; run every check with `labs/check.sh`.

- [ ] [Lab 01: FastAPI chat service with SSE streaming](labs/lab-01-fastapi-sse-chat/README.md)
- [ ] [Lab 02: Resilient HTTP client wrapper](labs/lab-02-resilient-http-client/README.md)
- [ ] [Lab 03: Test AWS code with moto](labs/lab-03-moto-aws-testing/README.md)

## Self-check (answer aloud, no notes)
- [ ] How do you make an LLM tool call idempotent when the agent retries?
- [ ] What happens to an asyncio service if one downstream call blocks the event loop?

## Folder layout
```
M01-python-engineering/
├── README.md          ← you are here
├── docs/
│   ├── guide.md       ← study guide
│   └── notes.md       ← your notes
└── labs/
    ├── SETUP.md       ← environment setup
    ├── lab-01-fastapi-sse-chat/
    ├── lab-02-resilient-http-client/
    └── lab-03-moto-aws-testing/
```
