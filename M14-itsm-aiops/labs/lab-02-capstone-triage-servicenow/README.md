# M14 · Lab 02: Capstone triage agent against ServiceNow

> Module: [ITSM, CloudOps, SRE and AIOps Use Cases](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)

## Goal
Run the capstone triage agent against your ServiceNow instance.

## Steps
1. Trigger: poll for new incidents (simple) or a ServiceNow outbound REST/business rule (advanced).
2. Agent: categorise, search runbooks/KB, propose diagnosis as a work note, request approval for any action.
3. Compare agent triage with your ground-truth labels: accuracy per field.
4. Measure time-to-triage and estimate analyst minutes saved per incident.

## Done when
- [ ] Accuracy table + value estimate you could present to a customer
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Correlate a CloudWatch alarm with an incident automatically.

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
