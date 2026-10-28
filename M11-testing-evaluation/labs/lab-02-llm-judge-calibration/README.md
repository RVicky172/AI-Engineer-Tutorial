# M11 · Lab 02: LLM-as-judge vs your own scoring

> Module: [Testing and Evaluation of Agentic Systems](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)

## Goal
Write an LLM-as-judge rubric, then compare its scores with your manual scoring on 15 cases.

## Steps
1. Rubric: 3-4 criteria (correctness, groundedness, actionability, safety), each 1-5 with anchored descriptions.
2. Score 15 agent outputs yourself first (blind to the judge).
3. Judge prompt: rubric + reference answer + output; ask for reasoning then a structured score.
4. Compute agreement: exact, within-1, Cohen's kappa.
5. Probe biases: longer answers, answer order, same-model self-preference.
6. Revise the rubric once and re-measure.

## Done when
- [ ] Agreement numbers before/after rubric revision
- [ ] List of judge failure patterns
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Use a different model family as judge and compare.

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
