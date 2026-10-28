# M06 · Lab 03: Outbound OAuth with AgentCore Identity

> Module: [Amazon Bedrock AgentCore](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)

## Goal
Add outbound OAuth through AgentCore Identity so the agent calls a third-party API on behalf of a user.

## Steps
1. Pick a provider with a free OAuth app (e.g. GitHub or Google).
2. Create an OAuth2 credential provider in AgentCore Identity with the client ID/secret.
3. In a tool, request a user-scoped access token (e.g. the SDK's `requires_access_token` decorator, USER_FEDERATION flow); handle the authorization URL callback.
4. Call the third-party API (e.g. list the user's repositories).
5. Write down: inbound auth (who may call the agent) vs outbound auth (what the agent may call, as whom), and where tokens are stored.

## Done when
- [ ] Agent returns data fetched with the user's delegated token
- [ ] Explanation of inbound vs outbound auth in your own words
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Add a machine-to-machine (client credentials) provider for a second API and compare.

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
