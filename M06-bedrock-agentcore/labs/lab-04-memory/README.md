# M06 · Lab 04: AgentCore Memory across sessions

> Module: [Amazon Bedrock AgentCore](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)

## Goal
Enable Memory and show the agent recalling a user preference across two separate sessions.

## Steps
1. Create a memory resource with short-term events plus a long-term strategy (e.g. user preferences, semantic facts, summaries).
2. Write conversation events with `actor_id` and `session_id`.
3. Session 1: user states a preference ('I'm on the payments team, always show me P1s first').
4. Session 2 (new session ID, same actor): retrieve relevant long-term records and inject them into the prompt; verify recall.
5. Inspect the extracted records; define what must NOT be stored (secrets, raw PII) and how you would enforce it.

## Done when
- [ ] Transcript of two sessions showing recall
- [ ] A short 'memory policy' (what to store, retention, deletion)
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Delete a user's memory records (right-to-be-forgotten) and prove they are gone.

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
