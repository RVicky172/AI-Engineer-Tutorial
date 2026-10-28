# M09 · Lab 04: Lambda vs ECS for the same service

> Module: [Deployment: Docker, ECS/EKS/Lambda, CI/CD and IaC](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)

## Goal
Deploy the same service on Lambda and on ECS; compare cold start, cost and operational effort.

## Steps
1. Deploy the FastAPI app on Lambda (Mangum or AWS Lambda Web Adapter) behind a Function URL or API Gateway.
2. Measure cold start (`Init Duration` in REPORT logs) and warm latency.
3. Load test both with Locust at the same rate.
4. Estimate monthly cost for 3 traffic profiles with the AWS Pricing Calculator.
5. Note limits: Lambda timeout, payload size, streaming support, long-running agents.

## Done when
- [ ] `comparison.md` with numbers and a recommendation per traffic profile
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Add AgentCore Runtime as a third column.

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
