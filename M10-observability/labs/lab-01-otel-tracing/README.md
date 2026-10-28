# M10 · Lab 01: End-to-end OpenTelemetry traces for an agent

> Module: [Observability and Production Troubleshooting](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)

## Goal
Instrument your agent with OpenTelemetry and view traces end to end (request, model call, each tool call).

## Steps
1. Configure a `TracerProvider` with an OTLP exporter to local Jaeger; set `service.name`.
2. Auto-instrument FastAPI, httpx and botocore.
3. Add manual spans: `agent.run`, `llm.call` (attributes: `gen_ai.request.model`, `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`), `tool.<name>` (args summary, status).
4. Propagate context to the downstream tool API and see one connected trace.
5. Record exceptions on spans and set error status.
6. Switch the exporter to AWS (ADOT / CloudWatch) and find the same trace there.

## Done when
- [ ] One trace screenshot showing request -> model -> tools -> downstream API
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Add log correlation: every log line carries `trace_id` and `span_id`.

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
