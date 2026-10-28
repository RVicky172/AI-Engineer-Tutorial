# M05 · Lab 02: Bedrock Guardrails: PII masking and denied topics

> Module: [Amazon Bedrock](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)

## Goal
Attach a Guardrail that masks PII and blocks one denied topic; test with adversarial prompts and record the results.

## Steps
1. Create a guardrail (console or `bedrock.create_guardrail`): PII filter (anonymize EMAIL, PHONE; block credit-card numbers), one denied topic, prompt-attack content filter.
2. Create a version and attach it via `guardrailConfig` in Converse.
3. Also call the standalone `ApplyGuardrail` API on text to see how to use it outside model calls (e.g. on tool output).
4. Write 15 adversarial prompts: obfuscated PII, topic paraphrases, role-play, multi-turn attempts.
5. Record: blocked / masked / passed, and the `trace` showing which policy fired.

## Done when
- [ ] Results table for 15 prompts with false positives/negatives called out
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Add a contextual grounding check to a RAG answer and find its threshold trade-off.

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
