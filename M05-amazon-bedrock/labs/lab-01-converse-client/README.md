# M05 · Lab 01: Converse client with tool use, streaming and throttling retries

> Module: [Amazon Bedrock](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)

## Goal
Write a boto3 client that calls Converse with tool use, streams the response, and retries on throttling.

## Steps
1. Call `bedrock-runtime.converse` with a system prompt, messages and `inferenceConfig` (maxTokens, temperature).
2. Use an inference profile ID (cross-region) instead of a raw model ID and note why.
3. Implement the tool-use loop: `stopReason == 'tool_use'` -> run tool -> send `toolResult` -> repeat until `end_turn` (with a max-iterations guard).
4. Implement `converse_stream` and print text deltas as they arrive; collect `metadata.usage` at the end.
5. Configure botocore `Config(retries={'mode': 'adaptive', 'max_attempts': ...})` and add your own backoff for `ThrottlingException`.
6. Log modelId, input/output tokens, latency, stopReason per call.

## Done when
- [ ] A script that answers a question requiring 2 tool calls, streamed to the terminal
- [ ] Throttling retry path is unit-tested (stub the client)
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Replace the fake LLM in your M01 FastAPI service with this streaming client.

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
