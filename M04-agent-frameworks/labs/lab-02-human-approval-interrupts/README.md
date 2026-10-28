# M04 · Lab 02: Human approval with LangGraph interrupts

> Module: [Agent Frameworks and Multi-Agent Systems](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)

## Goal
Add a human approval step before any state-changing tool (restart service, close ticket).

## Steps
1. Tag tools as `read` or `write`.
2. Before executing a write tool, call `interrupt({...action details...})` inside the node.
3. Compile the graph with a checkpointer (start with `InMemorySaver`, then `SqliteSaver`) and run with a `thread_id`.
4. Resume with `Command(resume={'approved': True/False, 'comment': ...})`.
5. Handle rejection: the agent must explain and choose a safe alternative (e.g. add a comment, escalate).
6. Test: approve path, reject path, and resume after a process restart (SQLite checkpointer).

## Done when
- [ ] No write tool can run without an explicit approval record
- [ ] Resume works after restarting the Python process
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Allow the approver to edit the tool arguments before approving.

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
