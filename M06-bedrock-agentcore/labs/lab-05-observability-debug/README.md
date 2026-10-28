# M06 · Lab 05: Find a failing tool call in AgentCore Observability

> Module: [Amazon Bedrock AgentCore](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)

## Goal
Turn on Observability, trigger a failing tool call, and find the failure in the trace in under five minutes.

## Steps
1. Enable CloudWatch Transaction Search (one-time) and add ADOT (`aws-opentelemetry-distro`) instrumentation to the agent.
2. Redeploy and generate normal traffic.
3. Introduce a fault in one tool (e.g. raise on a specific input).
4. Start a timer; find the failing session, trace and span in the CloudWatch GenAI Observability views.
5. Write a 5-line RCA: symptom, evidence (span/attributes), root cause, fix, prevention.

## Done when
- [ ] Diagnosis under 5 minutes, RCA committed
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Add custom span attributes (ticket ID, tool name, tenant) and filter traces by them.

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
