# M04 · Lab 03: Supervisor with knowledge and actions agents

> Module: [Agent Frameworks and Multi-Agent Systems](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)

## Goal
Build a supervisor agent that delegates to a 'knowledge' agent and an 'actions' agent; test what happens when a sub-agent fails.

## Steps
1. Knowledge agent: only retrieval tools. Actions agent: only write tools (with approval).
2. Supervisor: uses the two agents as tools (Strands agents-as-tools) or LangGraph supervisor routing.
3. Inject failures: sub-agent raises, times out, returns garbage, returns 'I don't know'.
4. Observe and fix: supervisor must not loop, must report partial results, must respect a global step/time budget.
5. Record each failure mode and the behaviour before/after your fix.

## Done when
- [ ] Failure-mode table with before/after behaviour
- [ ] Global budget enforced (steps and wall-clock)
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Compare shared vs. isolated memory between agents: what leaks, what gets lost?

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
