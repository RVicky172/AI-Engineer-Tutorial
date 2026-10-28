# M06 · Amazon Bedrock AgentCore

**Priority:** Must have (differentiator) · **Roadmap week:** 5

AgentCore is the central platform in this job description. Candidates who have actually deployed an agent on AgentCore stand out. Read the current AWS documentation, because this service evolves quickly.

## How to work through this module
1. **Study** — read [docs/guide.md](docs/guide.md) and write key points in your own words in [docs/notes.md](docs/notes.md).
2. **Set up** — follow [labs/SETUP.md](labs/SETUP.md).
3. **Practise** — do the labs in order (at least the first two before moving on).
4. **Check** — answer the self-check questions out loud without notes, then update [PROGRESS.md](../PROGRESS.md).

## Labs
- [ ] [Lab 01: Deploy an agent to AgentCore Runtime](labs/lab-01-deploy-runtime/README.md)
- [ ] [Lab 02: Put your REST API behind AgentCore Gateway](labs/lab-02-gateway-openapi-target/README.md)
- [ ] [Lab 03: Outbound OAuth with AgentCore Identity](labs/lab-03-identity-outbound-oauth/README.md)
- [ ] [Lab 04: AgentCore Memory across sessions](labs/lab-04-memory/README.md)
- [ ] [Lab 05: Find a failing tool call in AgentCore Observability](labs/lab-05-observability-debug/README.md)

## Self-check (answer aloud, no notes)
- [ ] What is the difference between inbound and outbound authentication for an agent?
- [ ] Where would you put a rule that forbids the agent from deleting records, and why there?

## Folder layout
```
M06-bedrock-agentcore/
├── README.md          ← you are here
├── docs/
│   ├── guide.md       ← study guide
│   └── notes.md       ← your notes
└── labs/
    ├── SETUP.md       ← environment setup
    ├── lab-01-deploy-runtime/
    ├── lab-02-gateway-openapi-target/
    ├── lab-03-identity-outbound-oauth/
    ├── lab-04-memory/
    └── lab-05-observability-debug/
```
