# M06 · Lab 02: Put your REST API behind AgentCore Gateway

> Module: [Amazon Bedrock AgentCore](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)

## Goal
Expose your own FastAPI service (with an OpenAPI spec) through AgentCore Gateway and call it from the agent as an MCP tool.

## Steps
1. Build a small mock ticketing API in FastAPI and export `openapi.json`. Host it somewhere reachable (e.g. Lambda + Function URL / API Gateway).
2. Create a Gateway with inbound auth (e.g. Cognito JWT authorizer).
3. Add a target: OpenAPI spec (with outbound API-key/OAuth credentials) or a Lambda target.
4. From the agent, connect an MCP client (streamable HTTP) to the Gateway URL with a bearer token; list tools; call one.
5. Trigger an upstream error and see what the agent receives.

## Done when
- [ ] Agent lists and calls tools that come from your OpenAPI spec via the Gateway
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Try semantic tool search on the Gateway with 20+ tools.

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
