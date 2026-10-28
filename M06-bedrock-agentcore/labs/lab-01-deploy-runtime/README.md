# M06 · Lab 01: Deploy an agent to AgentCore Runtime

> Module: [Amazon Bedrock AgentCore](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)

## Goal
Deploy a Strands or LangGraph agent to AgentCore Runtime, invoke it from Python and stream the response.

## Steps
1. Wrap your agent: `app = BedrockAgentCoreApp()`, decorate the handler with `@app.entrypoint`, call `app.run()`.
2. Run locally and POST to `localhost:8080/invocations` to test.
3. Configure and deploy with the starter toolkit (`agentcore configure ...`, then `agentcore launch`); note the IAM execution role it creates.
4. Invoke with `agentcore invoke '{"prompt": "..."}'`.
5. Invoke from boto3 (`bedrock-agentcore` client, `invoke_agent_runtime`) with a `runtimeSessionId`; stream the response.
6. Call twice with the same session ID and with a different one; observe session isolation.

## Done when
- [ ] A Python client that streams a response from the deployed agent
- [ ] Architecture note: what AgentCore created for you (ECR, role, runtime, endpoint)
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Deploy a new version and route the endpoint to it; then roll back.

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
