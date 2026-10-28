# M02 · Lab 02: Tool design for an IT-support agent

> Module: [LLM Fundamentals, Prompting, Tool Calling and Structured Outputs](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)

## Goal
Design five tools (get_ticket, search_kb, restart_service, add_comment, escalate) and measure how often the model picks the right one.

## Steps
1. Write v1 tool definitions quickly (one-line descriptions).
2. Create 25 user requests labelled with the expected tool (include ambiguous ones and ones that need no tool).
3. Run each request once and record which tool (and arguments) the model chose.
4. Write v2 definitions: when to use / when NOT to use, argument formats with examples, enums instead of free text.
5. Re-run and compare selection accuracy and argument validity.
6. Implement error results: return `is_error`/status with a short actionable message and observe how the model recovers.

## Done when
- [ ] Accuracy table v1 vs v2
- [ ] A short list of the description changes that made the biggest difference
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Allow parallel tool calls and test a request that needs two tools at once.

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
