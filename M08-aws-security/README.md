# M08 · AWS Security: IAM, OAuth, Secrets and Network

**Priority:** Must have · **Roadmap week:** 6

Customer security reviews decide whether you go live. Most integration delays come from IAM, secrets or private connectivity.

## How to work through this module
1. **Study** — read [docs/guide.md](docs/guide.md) and write key points in your own words in [docs/notes.md](docs/notes.md).
2. **Set up** — follow [labs/SETUP.md](labs/SETUP.md).
3. **Practise** — do the labs in order (at least the first two before moving on).
4. **Check** — answer the self-check questions out loud without notes, then update [PROGRESS.md](../PROGRESS.md).

## Labs
- [ ] [Lab 01: Least-privilege role for an agent](labs/lab-01-least-privilege-agent-role/README.md)
- [ ] [Lab 02: Private Lambda reaching AWS only through VPC endpoints](labs/lab-02-private-lambda-endpoints/README.md)
- [ ] [Lab 03: Break it, diagnose it, write the runbook](labs/lab-03-accessdenied-runbook/README.md)

## Self-check (answer aloud, no notes)
- [ ] A Lambda times out calling Secrets Manager from a private subnet. List your checks in order.
- [ ] Explain the difference between a trust policy and a permissions policy.

## Folder layout
```
M08-aws-security/
├── README.md          ← you are here
├── docs/
│   ├── guide.md       ← study guide
│   └── notes.md       ← your notes
└── labs/
    ├── SETUP.md       ← environment setup
    ├── lab-01-least-privilege-agent-role/
    ├── lab-02-private-lambda-endpoints/
    └── lab-03-accessdenied-runbook/
```
