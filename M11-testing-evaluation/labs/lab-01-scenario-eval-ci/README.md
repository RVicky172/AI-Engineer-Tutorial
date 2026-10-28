# M11 · Lab 01: 40-case scenario evaluation gated in CI

> Module: [Testing and Evaluation of Agentic Systems](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)

## Goal
Build a 40-case scenario evaluation set for your triage agent and run it in CI; fail the build if success rate drops by more than 5 points.

## Steps
1. Scenario schema (YAML): input incident, mocked tool responses, expected tool calls, forbidden tool calls, success assertions on the final answer.
2. Write 40 scenarios: easy, ambiguous, tool failure, missing data, adversarial.
3. Runner: replaces real tools with recorders, runs the agent, scores task success and tool-selection accuracy.
4. Run each scenario 3x; report mean and flakiness.
5. Store `baseline.json`; CI compares and fails if success rate drops > 5 points.

## Done when
- [ ] CI job that fails on a deliberately bad prompt change
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Track cost and latency per scenario and gate on them too.

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
