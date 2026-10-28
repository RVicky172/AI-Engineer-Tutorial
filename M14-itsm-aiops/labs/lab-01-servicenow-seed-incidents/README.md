# M14 · Lab 01: Seed 20 realistic incidents

> Module: [ITSM, CloudOps, SRE and AIOps Use Cases](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)

## Goal
Script the creation of 20 sample incidents on your ServiceNow developer instance.

## Steps
1. Design 20 incidents across categories (network, database, application, access), priorities (impact x urgency) and CIs.
2. Script creation via the Table API; set `correlation_id` so the script is idempotent (skip if exists).
3. Add a cleanup script that deletes only your seeded records.
4. Label each incident with your 'ground truth' triage (category, assignment group, likely runbook) in a local file.

## Done when
- [ ] Re-running the seed does not create duplicates; cleanup works
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Seed matching knowledge articles (`kb_knowledge`).

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
