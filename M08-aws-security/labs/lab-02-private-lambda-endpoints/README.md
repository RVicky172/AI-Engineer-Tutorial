# M08 · Lab 02: Private Lambda reaching AWS only through VPC endpoints

> Module: [AWS Security: IAM, OAuth, Secrets and Network](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)

## Goal
Deploy a Lambda in a private VPC that reaches Bedrock, S3 and Secrets Manager only through VPC endpoints.

## Steps
1. Start from the M05 lab-04 VPC (no NAT).
2. Add interface endpoints: `bedrock-runtime`, `secretsmanager` (private DNS on); gateway endpoint: S3 (route table association).
3. Security groups: endpoint SG allows 443 from Lambda SG only.
4. Add endpoint policies that allow only your role and resources.
5. Lambda reads a secret, reads an S3 object, calls Bedrock. All succeed.
6. Remove one endpoint and record the exact failure symptom (usually a timeout, not AccessDenied).

## Done when
- [ ] Success logs + recorded failure symptom per missing endpoint
- [ ] Everything destroyed afterwards
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Add a bucket policy that denies access unless `aws:SourceVpce` matches your endpoint.

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
