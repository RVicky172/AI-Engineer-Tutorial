# M09 Lab Environment Setup

## Prerequisites
- Docker Desktop
- Terraform >= 1.6
- A GitHub account + repository for this tutorial
- AWS sandbox account

## Python environment
From this `labs/` folder:

```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt
```

## AWS checklist
- [ ] `aws sts get-caller-identity` returns your **sandbox** account
- [ ] Default region set (`aws configure get region`) and the services you need are available there
- [ ] AWS Budget alarm exists
- [ ] Copy `.env.example` to `.env` and fill it in (`.env` is git-ignored)
- [ ] Delete billable resources at the end of each session (endpoints, vector stores, NAT gateways, load balancers)

## Labs in this module
- [Containerise and deploy to ECS Fargate with Terraform](lab-01-docker-ecs-terraform/README.md)
- [CI/CD with promotion and one-command rollback](lab-02-cicd-pipeline/README.md)
- [Step Functions with retries and a dead-letter queue](lab-03-step-functions-dlq/README.md)
- [Lambda vs ECS for the same service](lab-04-lambda-vs-ecs/README.md)
