# M04 · Lab 01: Incident triage agent in LangGraph and Strands

> Module: [Agent Frameworks and Multi-Agent Systems](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)

## Goal
Build the same IT incident triage agent in LangGraph and in Strands Agents; compare code size, debuggability and trace clarity.

## Steps
1. Create `shared/tools.py` with mock tools over in-memory data: `get_ticket`, `search_kb`, `get_service_status`, `restart_service`, `add_comment`.
2. Create 10 test incidents with the expected diagnosis and expected tool sequence.
3. LangGraph: explicit `StateGraph` with nodes (classify, retrieve, decide, act) and conditional edges.
4. Strands: one `Agent` with the same tools (`@tool` decorator) and a system prompt.
5. Add a max-step guard in both.
6. Run all 10 incidents in both and log every step.
7. Write `comparison.md`: LOC, how you debugged a wrong step, trace readability, determinism, which you would pick for which customer.

## Done when
- [ ] Both implementations solve >= 8/10 incidents
- [ ] `comparison.md` with a clear recommendation
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Rebuild the LangGraph version as `create_react_agent` (prebuilt) and compare with your explicit graph.

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
