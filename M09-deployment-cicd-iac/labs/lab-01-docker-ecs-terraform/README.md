# M09 · Lab 01: Containerise and deploy to ECS Fargate with Terraform

> Module: [Deployment: Docker, ECS/EKS/Lambda, CI/CD and IaC](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)

## Goal
Containerise your agent service and deploy it to ECS Fargate with Terraform, including task role, logs and a load-balancer health check.

## Steps
1. Multi-stage Dockerfile: builder installs deps with uv; runtime is slim, runs as non-root, has a HEALTHCHECK.
2. Terraform: remote state in S3, ECR repo with scan-on-push, VPC (community module is fine), ECS cluster, task definition, service, ALB + target group on `/health`, log group.
3. Separate execution role (pull image, write logs) from task role (Bedrock, secrets).
4. `terraform plan` -> `apply`; hit the ALB URL.
5. `terraform destroy` when done.

## Done when
- [ ] Service reachable via ALB; healthy targets
- [ ] Image < 300 MB, runs as non-root, no critical scan findings
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Turn the ECS service into a reusable Terraform module with variables per environment.

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
