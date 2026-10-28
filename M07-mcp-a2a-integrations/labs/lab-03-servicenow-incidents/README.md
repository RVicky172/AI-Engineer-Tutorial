# M07 · Lab 03: ServiceNow incident tools

> Module: [MCP, A2A and Enterprise Integrations](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)

## Goal
Build tools for creating, reading and updating ServiceNow incidents on your Personal Developer Instance.

## Steps
1. Create a PDI; store instance URL and credentials in env vars (later Secrets Manager).
2. Use the Table API: `GET/POST/PATCH /api/now/table/incident` with `sysparm_query`, `sysparm_fields`, `sysparm_limit`, `sysparm_offset`.
3. Tools: `create_incident`, `get_incident(number)`, `search_incidents(query)`, `add_work_note(number, text)`.
4. Return compact, model-friendly results (only needed fields, display values).
5. Expose them via your MCP server from lab-01.

## Done when
- [ ] Agent creates an incident, finds it again, and adds a work note
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Read CMDB CIs (`cmdb_ci_service`) to enrich an incident.

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
