# M05 · Lab 03: Model invocation logging and a token/latency query

> Module: [Amazon Bedrock](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)

## Goal
Enable model invocation logging and build a CloudWatch query that shows tokens and latency per request.

## Steps
1. Enable model invocation logging to CloudWatch Logs (and optionally S3) in Bedrock settings; create the IAM role it needs.
2. Generate ~50 requests across two models.
3. Write a Logs Insights query: tokens in/out, latency, by modelId, p50/p95.
4. Add the query as a widget on a CloudWatch dashboard.
5. Note what sensitive content ends up in these logs and how you would restrict access.

## Done when
- [ ] Saved Logs Insights query + dashboard screenshot
- [ ] A note on log data sensitivity and retention
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Estimate daily cost from the token counts with a query-side calculation.

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
