# M10 · Lab 03: Game day: five faults, timed diagnosis

> Module: [Observability and Production Troubleshooting](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)

## Goal
Introduce five faults and time how long each takes to diagnose.

## Steps
1. Implement fault switches (env vars / feature flags): expired secret, wrong IAM permission, slow API (+5s), bad prompt change, empty retrieval.
2. Ask a friend (or a script) to enable one at random without telling you which.
3. Diagnose using only dashboards, logs and traces. Time it.
4. Fill `postmortem.md` per fault: symptom, detection, diagnosis path, root cause, fix, prevention, time-to-diagnose.

## Done when
- [ ] Five postmortems; average time-to-diagnose noted
- [ ] One improvement to your telemetry per fault
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Repeat a week later and compare times.

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
