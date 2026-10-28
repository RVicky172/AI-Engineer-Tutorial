# M12 · Lab 02: Approval gate and audit log for state-changing tools

> Module: [Responsible AI, Security and Data Protection](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)

## Goal
Add a human-approval gate and an audit log for any tool that changes state.

## Steps
1. Classify every tool as read / write / destructive.
2. Decorator/middleware enforcing approval for write+destructive tools (no bypass path through the model).
3. Audit record: timestamp, actor (user), agent session, trace ID, tool, redacted args, approval decision + approver, result.
4. Append-only store (JSONL locally; DynamoDB or S3 with Object Lock in AWS).
5. Tests: unapproved write is blocked; audit entry exists for every write attempt (approved or not); secrets never appear in the log.

## Done when
- [ ] Tests prove the gate cannot be bypassed and every attempt is audited
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Make approvals expire and bind them to exact arguments (hash).

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
