# M05 · Lab 04: Call Bedrock from a private subnet via VPC endpoint

> Module: [Amazon Bedrock](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)

## Goal
Create a VPC endpoint for Bedrock Runtime and prove a Lambda in a private subnet can call it with no internet route.

## Steps
1. Create a VPC with private subnets only (no NAT gateway, no internet gateway route).
2. Create an interface endpoint for `com.amazonaws.<region>.bedrock-runtime` with private DNS enabled; security group allows 443 from the Lambda SG.
3. Deploy a Lambda into the private subnets that calls Converse.
4. Prove isolation: the same Lambda times out calling a public URL (e.g. https://example.com).
5. Optional: add an endpoint policy restricting which models may be invoked.
6. Tear everything down (interface endpoints are billed per hour).

## Done when
- [ ] Lambda log showing a successful Converse call AND a failed public call
- [ ] Infrastructure as code committed (Terraform/CDK) or console steps documented
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Reuse this VPC in M08 lab-02 and add Secrets Manager and S3 endpoints.

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
