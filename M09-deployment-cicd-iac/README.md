# M09 · Deployment: Docker, ECS/EKS/Lambda, CI/CD and IaC

**Priority:** Must have · **Roadmap week:** 6

You own the path from a working prototype to a repeatable production release, including rollback.

## How to work through this module
1. **Study** — read [docs/guide.md](docs/guide.md) and write key points in your own words in [docs/notes.md](docs/notes.md).
2. **Set up** — follow [labs/SETUP.md](labs/SETUP.md).
3. **Practise** — do the labs in order (at least the first two before moving on).
4. **Check** — answer the self-check questions out loud without notes, then update [PROGRESS.md](../PROGRESS.md).

## Labs
- [ ] [Lab 01: Containerise and deploy to ECS Fargate with Terraform](labs/lab-01-docker-ecs-terraform/README.md)
- [ ] [Lab 02: CI/CD with promotion and one-command rollback](labs/lab-02-cicd-pipeline/README.md)
- [ ] [Lab 03: Step Functions with retries and a dead-letter queue](labs/lab-03-step-functions-dlq/README.md)
- [ ] [Lab 04: Lambda vs ECS for the same service](labs/lab-04-lambda-vs-ecs/README.md)

## Self-check (answer aloud, no notes)
- [ ] How would you roll back a release when the problem is a prompt change, not code?
- [ ] When would you choose EKS over ECS for a customer?

## Folder layout
```
M09-deployment-cicd-iac/
├── README.md          ← you are here
├── docs/
│   ├── guide.md       ← study guide
│   └── notes.md       ← your notes
└── labs/
    ├── SETUP.md       ← environment setup
    ├── lab-01-docker-ecs-terraform/
    ├── lab-02-cicd-pipeline/
    ├── lab-03-step-functions-dlq/
    └── lab-04-lambda-vs-ecs/
```
