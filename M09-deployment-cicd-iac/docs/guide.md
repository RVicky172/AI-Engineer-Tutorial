# M09 · Deployment: Docker, ECS/EKS/Lambda, CI/CD and IaC — Study Guide

> **Priority:** Must have · **Week:** 6 · **Study time:** ~3-4 h · **Labs:** [../labs](../labs/SETUP.md)

## Why it matters
You own the path from a working prototype to a **repeatable production release — including rollback**. For AI systems, "the release" is code *plus* prompts, tool schemas and model IDs.

## Learning objectives
- Build small, secure container images.
- Choose between Lambda, ECS Fargate, EKS and AgentCore Runtime with clear reasons.
- Build a CI/CD pipeline with environment promotion, approvals and rollback.
- Write Terraform you can run safely in CI.
- Use event-driven building blocks (EventBridge, Step Functions, SQS/SNS, DLQs).
- Release prompts/models safely.

---

## 1. Docker done right
```dockerfile
# ---- build stage ----
FROM python:3.12-slim AS build
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
RUN uv sync --frozen --no-dev

# ---- runtime stage ----
FROM python:3.12-slim
RUN useradd --create-home --uid 10001 app
WORKDIR /app
COPY --from=build --chown=app /app /app
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
USER app
EXPOSE 8000
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
CMD ["uvicorn", "chat_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
```
Checklist: multi-stage, slim base, pinned versions, **non-root user**, health check, `.dockerignore`, no secrets in layers, **ECR scan on push**, immutable tags (git SHA).

## 2. Choosing a runtime
| Runtime | Best for | Watch out |
|---|---|---|
| **Lambda** | event-driven, spiky, short tasks; glue | 15-min max, cold starts, payload limits, concurrency vs. DB connections |
| **ECS Fargate** | long-running HTTP/streaming services, workers; simple ops | you size tasks; pay while running |
| **EKS** | customer already runs Kubernetes; portability; complex scheduling | operational overhead; need K8s skills |
| **AgentCore Runtime** | agents: session isolation, long sessions, integrated identity/memory/observability | newer service; check limits/regions |

**Kubernetes basics for EKS:** Deployment (replicas, rolling update), Service (stable endpoint), Ingress/ALB controller, readiness/liveness probes, HPA (autoscaling), ConfigMap/Secret, **IRSA / EKS Pod Identity** (IAM role per service account).

## 3. CI/CD
```
push/PR → lint + unit tests + prompt/eval regression → build image (tag = git SHA) → scan → push ECR
       → deploy dev → smoke tests → [manual approval] → deploy prod (canary/blue-green) → monitor → auto-rollback on alarm
```
- **OIDC federation** from GitHub Actions/GitLab to AWS: short-lived credentials, trust policy restricted to repo + branch/environment. No long-lived keys.
- **Environment promotion:** the *same* artifact (image digest) moves dev → staging → prod; only config differs.
- **Blue/green:** new version alongside old; switch traffic; instant rollback by switching back.
- **Canary:** shift 5-10% traffic first, watch alarms, then the rest.
- **Rollback:** redeploy the previous image tag / task definition revision; must be **one command** and practised.

## 4. Infrastructure as Code: Terraform
| Concept | Notes |
|---|---|
| Providers | `aws` provider, pinned versions |
| **State** | remote in S3 with locking (S3 native lockfile in recent versions, or DynamoDB); encrypted; never commit state |
| Modules | reusable units (network, service); use registry modules for VPC |
| Workspaces / directories | separate environments (separate state per env) |
| Plan/apply in CI | `terraform fmt -check`, `validate`, `plan` on PR (comment the plan), `apply` after merge/approval |
| Drift | `plan` shows manual changes; avoid console edits |
Also know **CloudFormation/CDK** concepts (stacks, change sets, constructs) — many AWS customers use them.

## 5. Event-driven building blocks
| Service | Role |
|---|---|
| **EventBridge** | event bus + routing rules + schedules (e.g. CloudWatch alarm → triage workflow) |
| **Step Functions** | orchestration: retries with backoff, catch, parallel/map, human approval via task tokens, full execution history |
| **SQS** | buffering, decoupling, backpressure; **DLQ** for poison messages; visibility timeout > processing time |
| **SNS** | fan-out notifications |
Pattern for agents: EventBridge rule → Step Functions → agent invocation with `Retry` → `Catch` → DLQ → alarm on DLQ depth → redrive after fix.

## 6. Release management for AI
- **Version together:** code, prompt versions, tool schemas, model IDs, guardrail versions → one release identifier.
- **Prompts as config** with feature flags (AppConfig / Parameter Store / LaunchDarkly) so you can roll back a prompt **without a redeploy** — but still through review and evals.
- **Eval gates** in CI (M11) block regressions before prod.
- **Staged rollout** + monitoring of quality signals (task success, escalations, thumbs-down), not just 5xx.

---

## Self-check (try first, then open)
<details><summary>How would you roll back a release when the problem is a prompt change, not code?</summary>

If prompts are versioned config behind a flag: flip the active prompt version back to the last good one (fast, no redeploy), verify with smoke/eval cases, then fix forward through the normal pipeline. If prompts are baked into the image: redeploy the previous image tag. Either way, confirm via traces/eval metrics that behaviour recovered, and add the failing case to the regression suite. This is why prompts, tools and model IDs must be versioned together.
</details>

<details><summary>When would you choose EKS over ECS for a customer?</summary>

When the customer already runs Kubernetes and has platform/SRE skills and tooling (Helm, Argo CD, service mesh, policy engines), needs portability across clouds/on-prem, or requires K8s-native features (custom schedulers, operators, GPU scheduling ecosystems). Otherwise ECS Fargate is simpler to operate, and you shouldn't add K8s complexity for one service.
</details>

## Resources
- Docker docs: multi-stage builds, best practices; Amazon ECR image scanning
- Amazon ECS developer guide (Fargate, task roles, deployments); EKS best practices guide
- GitHub Actions: OIDC with AWS (`aws-actions/configure-aws-credentials`), environments & approvals
- HashiCorp Terraform AWS tutorials; `terraform-aws-modules/vpc`
- AWS Step Functions developer guide (error handling, Retry/Catch)

**Next:** [Lab environment setup](../labs/SETUP.md) → [Lab 01](../labs/lab-01-docker-ecs-terraform/README.md)
