# M07 · MCP, A2A and Enterprise Integrations — Study Guide

> **Priority:** Must have · **Week:** 5 · **Study time:** ~3 h · **Labs:** [../labs](../labs/SETUP.md)

## Why it matters
A Forward Deployment Engineer spends most of their time **integrating agents with customer systems**. When no connector exists, you build one — quickly, safely, and in a way the model can use reliably.

## Learning objectives
- Build and consume MCP servers (tools, resources, prompts) over stdio and streamable HTTP.
- Explain A2A and how it differs from MCP.
- Integrate REST APIs robustly: auth flows, pagination, rate limits, webhooks, errors.
- Read an unfamiliar API spec quickly and wrap it as good tools.
- Know the main enterprise systems (ITSM, monitoring, identity) you'll meet.

---

## 1. Model Context Protocol (MCP)
An open protocol (JSON-RPC 2.0) that standardises how AI apps connect to tools and data. **Write a connector once; any MCP-capable agent can use it.**

| Concept | Meaning |
|---|---|
| **Host / client** | the AI app (agent) and its connection to a server |
| **Server** | exposes capabilities |
| **Tools** | functions the model can call (model-controlled) |
| **Resources** | readable data by URI, e.g. `ticket://INC0012345` (app-controlled) |
| **Prompts** | reusable prompt templates (user-controlled) |
| **Transports** | **stdio** (local subprocess) and **streamable HTTP** (remote; replaces the older HTTP+SSE transport) |
| **Auth** | remote servers use OAuth 2.1-based authorization; local stdio servers rely on the process environment |

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ticketing")

@mcp.tool()
async def get_ticket(number: str) -> dict:
    """Fetch one incident by number (format INC0012345). Returns status, priority, summary."""
    return await api.get_ticket(number)

@mcp.resource("ticket://{number}")
async def ticket_resource(number: str) -> str:
    return (await api.get_ticket(number))["description"]

if __name__ == "__main__":
    mcp.run()                              # stdio; use transport="streamable-http" for remote
```
Test with **MCP Inspector**: `npx @modelcontextprotocol/inspector`.

**Why wrap a legacy API as MCP?** Reuse across agents/frameworks; one place for auth, validation, rate limiting, error mapping, logging and least privilege; compact model-friendly I/O; and it plugs into AgentCore Gateway and other platforms.

## 2. Agent-to-Agent (A2A)
An open protocol for **agents talking to other agents**, possibly from different vendors/frameworks.
- **Agent Card:** JSON metadata (usually at `/.well-known/agent-card.json`) describing an agent's skills, endpoint and auth requirements.
- **Tasks:** a client agent sends a task; the remote agent works on it (possibly long-running, with status updates/streaming) and returns messages/artifacts.
- **MCP vs A2A:** MCP = agent ↔ tools/data (the agent stays in control). A2A = agent ↔ agent (delegating a goal to an autonomous peer). They're complementary.

## 3. REST integration craft
| Topic | What to do |
|---|---|
| **Pagination** | offset/limit, cursor/next-token, Link headers; cap total pages so agents don't pull 100k rows |
| **Rate limits** | read headers (`X-RateLimit-*`, `Retry-After`); client-side token bucket shared across parallel tool calls; queue + backoff |
| **Webhooks** | verify signatures (HMAC), respond fast and process async (SQS), de-duplicate by event ID |
| **Idempotency** | idempotency keys on create calls; safe retries |
| **Contract testing** | validate responses against the OpenAPI schema; record/replay fixtures |

### OAuth 2.0 flows you must know
| Flow | Who | Use |
|---|---|---|
| **Client credentials** | service ↔ service | agent acts as itself (`POST /token` with client id/secret → access token) |
| **Authorization code + PKCE** | user delegates to an app | agent acts **on behalf of a user**, with consent and scopes |
| Refresh tokens | — | renew access without the user re-consenting |
| API keys | — | simple, but no user context and hard to scope/rotate |
| **mTLS** | — | both sides present certificates; common in banks/enterprises |

Token handling: cache until shortly before `expires_in`; single-flight refresh under concurrency; on 401, refresh once and retry; never log tokens; store secrets in Secrets Manager / AgentCore Identity.

## 4. Reading an unfamiliar API fast
1. Find auth, base URL, rate limits and error format first.
2. Skim the OpenAPI/YAML for the 3-5 endpoints your use case needs.
3. Make one call with `curl`/HTTPie and save real responses as fixtures.
4. Generate a client if the spec is good (`openapi-python-client`), otherwise hand-write a thin `httpx` wrapper.
5. Design **tools around user intents**, not 1:1 around endpoints (e.g. `find_open_incidents_for_service` rather than raw `GET /table/incident?sysparm_query=...`).

## 5. Enterprise systems you will meet
- **ServiceNow:** Table API (`/api/now/table/{table}`; `incident`, `change_request`, `problem`, `cmdb_ci*`, `kb_knowledge`), `sysparm_query` (encoded queries like `active=true^priority=1`), `sysparm_fields`, `sysparm_limit`, `sysparm_display_value`. Work notes vs. comments (internal vs. customer-visible).
- **Monitoring:** CloudWatch alarms, Datadog, Dynatrace — alert payloads, metric queries, event APIs.
- **Identity:** Okta, Microsoft Entra ID — OIDC/OAuth, groups for authorisation, SCIM.

## 6. Error mapping
Enterprise APIs return messy errors (HTML 500 pages, vague 400s). The model needs **short, actionable** messages:

| Upstream | Tool error to the model |
|---|---|
| 404 | `not_found`: "No incident INC0099999. Check the number or use search_incidents." |
| 401/403 | `auth_error`: "Not permitted to update this record." (not retryable; don't leak details) |
| 429 | `rate_limited`, retryable, with wait time — but handle retries in code, not via the model |
| 5xx HTML | `upstream_error`: "Ticketing system unavailable (HTTP 503). Try later or escalate." |
| Timeout | `timeout`, retryable |
Strip HTML, truncate, remove stack traces and secrets, include a hint.

---

## Self-check (try first, then open)
<details><summary>Why wrap a legacy API as an MCP tool instead of letting the agent call it directly?</summary>

Security (credentials stay server-side, least-privilege operations only, input validation, audit), reliability (retries, rate limiting, timeouts, error mapping in code), model usability (intent-shaped tools, compact outputs, good descriptions), and reuse (any MCP client/framework, AgentCore Gateway). Letting the model craft raw HTTP calls is brittle, hard to secure and hard to observe.
</details>

<details><summary>How do you handle an API that rate-limits at 10 requests per second when an agent fans out tool calls?</summary>

Put a shared token-bucket limiter (10 rps, small burst) in the tool/MCP layer so all parallel calls queue through it — distributed (e.g. Redis/DynamoDB) if multiple instances share the limit. Add a concurrency semaphore, honour `Retry-After` with backoff + jitter, cache reads, batch where the API allows, and design tools to fetch lists in one call instead of N single fetches. Expose `rate_limited` errors only if waiting exceeds the budget.
</details>

## Resources
- Model Context Protocol specification and official Python SDK (`mcp`); MCP Inspector
- A2A protocol specification and `a2a-sdk`
- OAuth 2.0 / 2.1 (RFC 6749, PKCE RFC 7636) — oauth.net summaries
- ServiceNow Developer site: REST Table API; Personal Developer Instance

**Next:** [Lab environment setup](../labs/SETUP.md) → [Lab 01](../labs/lab-01-mcp-server-ticketing/README.md)
