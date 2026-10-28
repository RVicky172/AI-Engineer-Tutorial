# M10 · Lab 02: Agent dashboard and alarms

> Module: [Observability and Production Troubleshooting](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)

## Goal
Build a CloudWatch dashboard with p50/p95 latency, error rate, tokens and estimated cost per day, plus two alarms.

## Steps
1. Emit metrics with Embedded Metric Format: `Latency`, `TimeToFirstToken`, `InputTokens`, `OutputTokens`, `ToolErrors`, `EstimatedCostUSD`, dimensions `Service`, `Model`.
2. Dashboard widgets: p50/p95 latency, error rate (metric math), tokens/day, cost/day, tool success rate.
3. Alarm 1: error rate > 5% for 5 minutes. Alarm 2: p95 latency above your SLO. Notify via SNS email.
4. Trigger both alarms on purpose and confirm notifications.

## Done when
- [ ] Dashboard JSON committed (or Terraform)
- [ ] Both alarms fired and recovered
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Add an anomaly-detection alarm on daily token usage.

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
