# M02 · Lab 01: One extraction task, three techniques

> Module: [LLM Fundamentals, Prompting, Tool Calling and Structured Outputs](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)

## Goal
Solve the same extraction task with a plain prompt, few-shot prompting and tool-use with a schema. Measure accuracy and token cost on 30 inputs.

## Steps
1. Create `data/tickets.jsonl`: 30 realistic IT-support emails (write or generate them) with ground truth: `service`, `severity` (P1-P4), `requester`, `summary`.
2. Define the target as a Pydantic model; this is your single source of truth for the schema.
3. Technique A: plain instruction prompt asking for JSON.
4. Technique B: same prompt + 3 few-shot examples in XML-delimited blocks.
5. Technique C: tool-use / structured output with the JSON schema from `Model.model_json_schema()`.
6. Parse every response with Pydantic; count parse failures separately from wrong values.
7. Record input/output tokens from the API `usage` field and compute cost from current pricing.
8. Write a results table: field accuracy, parse-failure rate, avg tokens, cost per 1k tickets.

## Done when
- [ ] `results.md` with the comparison table and a 3-sentence conclusion
- [ ] Script is re-runnable with one command
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Add a repair loop: on validation error, send the error back once and re-ask. How much does accuracy improve vs. cost?

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
