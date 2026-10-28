# M01 · Lab 03: Test AWS code with moto

> Module: [Python and Software Engineering Fundamentals](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)
>
> **Reference solution included** (`src/`, `tests/`, `NOTES.md`). Try the lab yourself first for 60-90 minutes, then compare. See [../../LEARNINGS.md](../../LEARNINGS.md) for how to study it.

## Goal
Test code that reads from S3 and Secrets Manager without touching a real AWS account.

## Steps
1. Write `load_config()` that reads a JSON secret from Secrets Manager and a YAML/JSON object from S3.
2. Add an in-process cache so the secret is fetched once per TTL.
3. Raise your own `ConfigError` (not a raw botocore error) when the secret or object is missing.
4. Create pytest fixtures using `moto.mock_aws()` that create the bucket, object and secret.
5. Set fake credentials in a fixture (`AWS_ACCESS_KEY_ID=testing`, region etc.) so no real call can happen.
6. Tests: happy path, missing secret, missing object, cache hit (assert only one API call).

## Done when
- [ ] Tests pass with your real AWS credentials removed/unset
- [ ] No test takes > 1s
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Use `botocore.stub.Stubber` for one test and compare it with moto: when would you prefer each?

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
