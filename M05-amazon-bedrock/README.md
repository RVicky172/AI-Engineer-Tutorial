# M05 · Amazon Bedrock

**Priority:** Must have · **Roadmap week:** 4

Bedrock is the model layer for every solution in this role. Know the APIs, quotas and production features, not just the console.

## How to work through this module
1. **Study** — read [docs/guide.md](docs/guide.md) and write key points in your own words in [docs/notes.md](docs/notes.md).
2. **Set up** — follow [labs/SETUP.md](labs/SETUP.md).
3. **Practise** — do the labs in order (at least the first two before moving on).
4. **Check** — answer the self-check questions out loud without notes, then update [PROGRESS.md](../PROGRESS.md).

## Labs
- [ ] [Lab 01: Converse client with tool use, streaming and throttling retries](labs/lab-01-converse-client/README.md)
- [ ] [Lab 02: Bedrock Guardrails: PII masking and denied topics](labs/lab-02-guardrails/README.md)
- [ ] [Lab 03: Model invocation logging and a token/latency query](labs/lab-03-invocation-logging-dashboard/README.md)
- [ ] [Lab 04: Call Bedrock from a private subnet via VPC endpoint](labs/lab-04-private-vpc-endpoint/README.md)

## Self-check (answer aloud, no notes)
- [ ] You see intermittent ThrottlingException in production. What are your options, in order?
- [ ] How would you route simple vs. complex requests to different models and measure the savings?

## Folder layout
```
M05-amazon-bedrock/
├── README.md          ← you are here
├── docs/
│   ├── guide.md       ← study guide
│   └── notes.md       ← your notes
└── labs/
    ├── SETUP.md       ← environment setup
    ├── lab-01-converse-client/
    ├── lab-02-guardrails/
    ├── lab-03-invocation-logging-dashboard/
    └── lab-04-private-vpc-endpoint/
```
