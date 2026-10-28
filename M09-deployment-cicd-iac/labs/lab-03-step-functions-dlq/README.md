# M09 · Lab 03: Step Functions with retries and a dead-letter queue

> Module: [Deployment: Docker, ECS/EKS/Lambda, CI/CD and IaC](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)

## Goal
Build a Step Functions workflow that calls an agent, retries on failure, and sends failed items to an SQS dead-letter queue.

## Steps
1. Lambda `invoke_agent` that sometimes fails (configurable).
2. State machine: Task with `Retry` (ErrorEquals, IntervalSeconds, BackoffRate, MaxAttempts, JitterStrategy) and `Catch` -> SQS SendMessage to the DLQ.
3. Feed a batch of items (Map state).
4. Inspect the DLQ, fix the cause, redrive.

## Done when
- [ ] Execution history showing retries and DLQ routing
- [ ] Redrive procedure documented
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Trigger the state machine from EventBridge on a CloudWatch alarm.

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
