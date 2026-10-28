# M02 · Lab 03: Prompt regression suite

> Module: [LLM Fundamentals, Prompting, Tool Calling and Structured Outputs](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)

## Goal
Build a 20-case regression suite that runs on every prompt change.

## Steps
1. Store prompts as versioned files: `prompts/triage/v1.md`, `v2.md`, with a `CURRENT` pointer.
2. Write `cases.yaml`: 20 inputs, each with checks (`json_valid`, `field_equals`, `contains`, `not_contains`, `max_tokens`).
3. Implement a pytest-parametrised runner that loads each case, calls the model, runs the checks.
4. Run with temperature 0 and run each case 3x to spot flaky cases.
5. Make a deliberate prompt change in v2 and diff the reports.

## Done when
- [ ] `pytest evals/` runs the whole suite; a failing check fails the run
- [ ] A report file shows pass/fail per case per prompt version
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Wire it into a GitHub Actions workflow that runs when `prompts/**` changes.

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
