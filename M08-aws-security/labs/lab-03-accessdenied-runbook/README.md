# M08 · Lab 03: Break it, diagnose it, write the runbook

> Module: [AWS Security: IAM, OAuth, Secrets and Network](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)

## Goal
Deliberately break a policy, diagnose the AccessDenied using CloudTrail, and write the steps as a runbook.

## Steps
1. Faults to inject one at a time: missing action, wrong resource ARN, KMS key policy missing the role, trust policy wrong, explicit deny in an endpoint/bucket policy.
2. For each: capture the error message, find the event in CloudTrail (`aws cloudtrail lookup-events` or Event history), identify which policy type denied.
3. Fix and verify.
4. Write `runbook.md`: a decision tree from symptom to policy type to fix.

## Done when
- [ ] `runbook.md` that a teammate could follow without you
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Repeat for a cross-account AssumeRole failure.

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
