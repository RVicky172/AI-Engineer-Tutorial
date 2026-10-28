# M06 · Amazon Bedrock AgentCore — Study Guide

> **Priority:** Must have (**differentiator**) · **Week:** 5 · **Study time:** ~4 h · **Labs:** [../labs](../labs/SETUP.md)

> ⚠️ AgentCore evolves quickly. Use this guide for the **concepts**; check the current *Amazon Bedrock AgentCore Developer Guide*, SDK README and AWS "What's New" for exact APIs, CLI commands, regions and features before each lab.

## Why it matters
AgentCore is the central platform in this job description: it's how AWS turns "an agent on my laptop" into "an agent in production" with hosting, tools, memory, identity, policy and observability. Having actually deployed on it is what makes you stand out.

## Learning objectives
- Explain each AgentCore component and which production problem it solves.
- Deploy a framework-agnostic agent to Runtime and invoke/stream it.
- Expose APIs/Lambdas as MCP tools through Gateway.
- Use Memory, Identity (inbound + outbound auth) and Policy correctly.
- Find failures with AgentCore Observability.

---

## 1. The big picture
```
              ┌──────────────── AgentCore ─────────────────┐
 caller ──▶  Identity (inbound auth) ──▶ Runtime (your agent, any framework/model)
                                            │      │       │
                                       Memory   Gateway   Built-in tools
                                     (short/long) (MCP)   (Code Interpreter, Browser)
                                            │      │
                                   Identity (outbound: OAuth / API keys to 3rd parties)
                                   Policy (which tool calls are allowed)
              Observability (traces, metrics, logs → CloudWatch / OTel)   Evaluations
```
Components are **modular**: you can use Runtime alone, or Gateway/Memory/Identity with an agent hosted elsewhere (ECS, Lambda, EKS).

## 2. Runtime
Serverless hosting for agents built with **any framework** (Strands, LangGraph, CrewAI, custom) and any model.
- Packaged as a container exposing an HTTP contract (`/invocations`, `/ping`); the SDK's `BedrockAgentCoreApp` does this for you.
- **Session isolation:** each `runtimeSessionId` runs in its own isolated environment (micro-VM); state doesn't leak between users.
- Supports long-running work and streaming responses; scales automatically.
- Versions and endpoints let you roll forward/back.

```python
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent

app = BedrockAgentCoreApp()
agent = Agent(system_prompt="You are an IT triage assistant.")

@app.entrypoint
def invoke(payload: dict):
    return {"result": str(agent(payload.get("prompt", "")))}

if __name__ == "__main__":
    app.run()          # local server on :8080 for testing
```
Typical starter-toolkit flow (verify current CLI): `agentcore configure -e agent.py` → `agentcore launch` → `agentcore invoke '{"prompt": "hi"}'`. From code: boto3 `bedrock-agentcore` client → `invoke_agent_runtime(agentRuntimeArn=..., runtimeSessionId=..., payload=...)`.

## 3. Gateway
Turns existing **APIs (OpenAPI specs), Smithy models and Lambda functions into MCP-compatible tools**, behind one MCP endpoint.
- **Inbound auth:** callers (agents) authenticate to the Gateway (e.g. OAuth/JWT via Cognito or your IdP).
- **Outbound auth:** Gateway authenticates to targets (IAM for Lambda, API key or OAuth for APIs) using Identity's credential providers.
- **Tool discovery:** agents list tools via MCP; semantic search helps when there are many tools.
- Why it matters: one secure, governed place for tools instead of custom glue in every agent.

## 4. Memory
| Type | What | Example |
|---|---|---|
| **Short-term** | raw events of the current session (turns, tool results) | conversation history within a ticket |
| **Long-term** | extracted, persistent records via **strategies** (e.g. user preferences, semantic facts, session summaries) | "Asha is on Payments and wants P1s first" |
Records are organised by **actor** and **session** (namespaces). Design questions: what is worth remembering, what must never be stored (secrets, raw PII, other users' data), retention, and how a user can be forgotten.

## 5. Identity
- **Inbound auth — who may call the agent:** IAM (SigV4) or JWT/OAuth from the customer's IdP (Cognito, Okta, Entra ID). The agent knows *who* the user is.
- **Outbound auth — what the agent may call, as whom:**
  - *Machine-to-machine* (client credentials / API keys) — the agent acts as itself.
  - *User-delegated* (OAuth authorization code, 3-legged) — the agent acts **on behalf of the user** with their consent and scopes.
- **Token vault:** credentials and user tokens are stored and refreshed by AgentCore, not in your code. The SDK offers decorators (e.g. `requires_access_token`) to fetch tokens inside tools.

## 6. Policy
Deterministic control over **which tool calls an agent may make, with which arguments, for which user** — enforced outside the model (at the Gateway), so a prompt injection can't talk its way past it. Policies are written in a declarative policy language (Cedar) and can be authored from natural language. Check the current docs for availability and syntax.

**Why put rules here instead of the prompt?** Prompts are suggestions to a probabilistic model; policy enforcement is deterministic, auditable and centrally managed.

## 7. Observability and Evaluations
- Traces/spans for each invocation: model calls, tool calls, latency, errors, token usage — in CloudWatch (GenAI observability views), built on **OpenTelemetry**. Enable CloudWatch Transaction Search and instrument with ADOT (`aws-opentelemetry-distro`); export to other OTel back-ends if the customer uses Datadog etc.
- **Evaluations:** built-in evaluators (e.g. helpfulness, correctness, tool selection) and custom evaluators scoring live or test traffic. Pair with your offline eval suite (M11).

## 8. Built-in tools
- **Code Interpreter:** sandboxed code execution (data analysis, calculations, file transforms).
- **Browser:** managed headless browser for web tasks without public APIs.
Use them when the alternative is running untrusted code or browsers yourself; prefer your own typed tools when a proper API exists (faster, cheaper, more deterministic).

## 9. When to choose AgentCore vs. ECS/Lambda
| AgentCore Runtime | ECS / Lambda |
|---|---|
| per-session isolation, long-running agent sessions, built-in identity/memory/observability integration | customer already standardised on ECS/EKS, needs full network/runtime control, or very custom serving |
| fastest path to a secure, governed agent | Lambda: short event-driven tasks (time limit), ECS: long-running services you operate |

---

## Self-check (try first, then open)
<details><summary>What is the difference between inbound and outbound authentication for an agent?</summary>

Inbound = authenticating and authorising the **caller of the agent** (user or system), e.g. a JWT from the customer's IdP or IAM SigV4; it establishes user identity and whether they may invoke it. Outbound = how the **agent authenticates to downstream tools/APIs**: as itself (client credentials, API key, IAM role) or on behalf of the user (OAuth delegated token with user consent and scopes). AgentCore Identity manages both, and vaults outbound tokens.
</details>

<details><summary>Where would you put a rule that forbids the agent from deleting records, and why there?</summary>

Defence in depth, with the **hard guarantee outside the model**: don't expose a delete tool at all (least privilege); if needed, enforce a Policy at the Gateway/tool layer that denies delete calls; and the downstream credential/IAM role should lack delete permission. The prompt can mention it, but prompts are not a security boundary — injection or model error could bypass it. Add audit logging and, for any destructive action, human approval.
</details>

## Resources
- Amazon Bedrock AgentCore Developer Guide (Runtime, Gateway, Memory, Identity, Policy, Observability, Evaluations, built-in tools)
- `bedrock-agentcore` Python SDK and `bedrock-agentcore-starter-toolkit` on GitHub/PyPI
- `awslabs/amazon-bedrock-agentcore-samples` on GitHub (tutorials per component)
- AWS "What's New" feed filtered for AgentCore

**Next:** [Lab environment setup](../labs/SETUP.md) → [Lab 01](../labs/lab-01-deploy-runtime/README.md)
