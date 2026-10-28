# M08 · Lab 01: Least-privilege role for an agent

> Module: [AWS Security: IAM, OAuth, Secrets and Network](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)

## Goal
Create a role for an agent with only the permissions it needs (one Bedrock model, one S3 prefix, one secret) and prove what is denied.

## Steps
1. Trust policy: allow only the compute service that runs the agent (e.g. `lambda.amazonaws.com`) to assume it.
2. Permissions: `bedrock:InvokeModel`/`InvokeModelWithResponseStream` on one model (and its inference profile) ARN; `s3:GetObject` on `arn:aws:s3:::bucket/agent-data/*`; `secretsmanager:GetSecretValue` on one secret ARN.
3. Use `aws iam simulate-principal-policy` to test 6 allowed and 6 denied actions/resources.
4. Run IAM Access Analyzer policy validation and fix warnings.

## Done when
- [ ] Allow/deny matrix committed with the simulator output
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Add a permission boundary and a condition key (e.g. `aws:SourceVpce`).

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
