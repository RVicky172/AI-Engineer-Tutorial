# M13 · Lab 01: Safe text-to-SQL tool

> Module: [Databases, SQL and Enterprise Data Sources](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)

## Goal
Build a text-to-SQL tool with a read-only role, schema description, row limit and query allow-list. Test with 10 tricky and 3 malicious questions.

## Steps
1. Connect as `agent_ro` (created in seed.sql: SELECT-only, read-only transactions, statement timeout).
2. Write a schema description (tables, columns, meaning, join keys, example values) for the prompt.
3. Generate SQL with the model (tool-use: `{sql, explanation}`).
4. Validate with sqlglot: exactly one statement, SELECT only, tables in allow-list, no system catalogs; inject/force `LIMIT 100`.
5. Execute, return rows + the SQL used.
6. 10 tricky questions (joins, window functions, date ranges, NULLs) + 3 malicious (DROP, read `pg_authid`/other tables, stacked statements).

## Done when
- [ ] Results table; all 3 malicious attempts blocked by at least two layers
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Add a self-correction loop that feeds SQL errors back once.

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
