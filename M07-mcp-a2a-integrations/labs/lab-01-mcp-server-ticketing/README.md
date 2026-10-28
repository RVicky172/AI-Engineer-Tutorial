# M07 · Lab 01: MCP server over a mock ticketing API

> Module: [MCP, A2A and Enterprise Integrations](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)

## Goal
Build an MCP server in Python that exposes three tools over a mock ticketing API and connect it to an agent.

## Steps
1. Use the official Python SDK (`from mcp.server.fastmcp import FastMCP`).
2. Expose tools `list_tickets(status, limit)`, `get_ticket(id)`, `add_comment(id, text)` and a resource `ticket://{id}`.
3. Run over stdio and test with MCP Inspector.
4. Switch to streamable HTTP transport and test again.
5. Connect a Strands agent (MCP client) and complete a task that needs all three tools.

## Done when
- [ ] Inspector screenshot listing tools
- [ ] Agent transcript using the tools over HTTP
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Add a prompt template (`@mcp.prompt`) for 'summarise this ticket'.

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
