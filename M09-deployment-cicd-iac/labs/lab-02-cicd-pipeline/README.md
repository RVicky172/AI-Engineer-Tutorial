# M09 · Lab 02: CI/CD with promotion and one-command rollback

> Module: [Deployment: Docker, ECS/EKS/Lambda, CI/CD and IaC](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)

## Goal
Pipeline: build -> test -> push to ECR -> deploy dev -> manual approval -> prod, with one-command rollback.

## Steps
1. GitHub Actions with OIDC federation to AWS (no long-lived keys); IAM role trust restricted to your repo/branch.
2. Jobs: lint + unit tests + prompt regression suite -> build image tagged with the git SHA -> push.
3. Deploy to dev; smoke test.
4. `prod` GitHub environment with required reviewer (manual approval).
5. Rollback workflow: redeploy a given previous image tag (`workflow_dispatch` input).
6. Version prompts, tool schemas and model IDs together with the code (one release = one SHA).

## Done when
- [ ] A green pipeline run through prod
- [ ] A rollback executed and timed
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Use ECS blue/green or canary deployment with automatic rollback on alarm.

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
