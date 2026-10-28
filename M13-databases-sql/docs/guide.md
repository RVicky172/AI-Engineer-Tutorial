# M13 · Databases, SQL and Enterprise Data Sources — Study Guide

> **Priority:** Must have · **Week:** 2 · **Study time:** ~3 h · **Labs:** [../labs](../labs/SETUP.md)

## Why it matters
Agents often need **structured data**: incident counts, service owners, change history, customer records. You must query it fluently and let an agent query it **safely**.

## Learning objectives
- Write intermediate/advanced SQL: joins, CTEs, window functions; read query plans.
- Explain transactions and isolation levels.
- Build a text-to-SQL tool with layered safety controls.
- Pick the right AWS data store/access pattern and connect to it reliably.
- Understand how enterprise data is organised (warehouses, lakes, CMDBs).

> Practice database: `docker compose up -d` in [../labs](../labs/SETUP.md) loads an ITSM schema (`teams`, `users`, `services`, `incidents`, `changes`) from [seed.sql](../labs/seed.sql).

---

## 1. SQL fluency
```sql
-- CTE + join + aggregation: open P1/P2 incidents per tier-1 service
WITH open_inc AS (
  SELECT * FROM incidents WHERE state IN ('new','in_progress') AND priority IN ('P1','P2')
)
SELECT s.name, count(*) AS open_high
FROM open_inc i JOIN services s ON s.id = i.service_id
WHERE s.tier = 1
GROUP BY s.name
ORDER BY open_high DESC;

-- Window functions: mean time to resolve per service + rank, and each incident vs. its service average
SELECT number, service_id,
       resolved_at - opened_at                                        AS ttr,
       avg(resolved_at - opened_at) OVER (PARTITION BY service_id)     AS avg_ttr_service,
       rank() OVER (PARTITION BY service_id ORDER BY opened_at DESC)   AS recency_rank
FROM incidents
WHERE resolved_at IS NOT NULL;

-- Did a failed change precede incidents on the same service within 24h?
SELECT c.number, i.number
FROM changes c
JOIN incidents i ON i.service_id = c.service_id
 AND i.opened_at BETWEEN c.scheduled_at AND c.scheduled_at + interval '24 hours'
WHERE c.succeeded = false;
```
Know: `INNER/LEFT` joins and NULL behaviour, `GROUP BY`/`HAVING`, window functions (`row_number`, `rank`, `lag/lead`, running sums), `EXPLAIN ANALYZE`, B-tree indexes (and when they're not used: functions on columns, leading wildcards, low selectivity).

## 2. Transactions and isolation
- **ACID**; `BEGIN … COMMIT/ROLLBACK`.
- Isolation levels: Read Committed (PostgreSQL default), Repeatable Read, Serializable — trade consistency for concurrency. Know the anomalies: dirty read, non-repeatable read, phantom, lost update.
- For agents: read-only transactions for queries; any write goes through a dedicated, reviewed tool — never free-form SQL.

## 3. Text-to-SQL agents: layered safety
| Layer | Control |
|---|---|
| **Database** | read-only role (`GRANT SELECT` on specific tables/columns), `default_transaction_read_only`, `statement_timeout`, row-level security, a **read replica** not the primary |
| **Schema grounding** | curated schema description (tables, columns, meanings, join keys, sample values) — or curated **views** that hide sensitive columns |
| **Validation** | parse SQL (e.g. `sqlglot`): single statement, `SELECT` only, allow-listed tables, no system catalogs/functions, enforce `LIMIT` |
| **Execution** | timeouts, row/byte caps, connection pool limits |
| **Output** | return the SQL used + results; summarise large results; mask sensitive values |
| **Monitoring** | log queries (without sensitive results), alert on rejected/malicious attempts |

Each layer assumes the one before can fail. The DB role is the hard guarantee.

## 4. AWS data stores and access patterns
| Store | Use | Agent notes |
|---|---|---|
| **RDS / Aurora PostgreSQL** (+ pgvector) | relational, transactional, also vectors | use RDS Proxy for many short-lived clients; IAM DB auth or Secrets Manager rotation |
| **DynamoDB** | key-value at scale, known access patterns | design keys around queries (PK/SK, GSIs); great for sessions, idempotency records, audit logs |
| **S3 + Athena** | data lake, analytics with SQL over files (Parquet) | pay per data scanned; partition + columnar formats |
| **Redshift** | data warehouse | analytic queries; keep agents to curated views |
| Aurora Data API / Redshift Data API | HTTP-based SQL without connection management | handy from Lambda |

## 5. Enterprise data sources
- **Data warehouses/lakes:** curated, modelled (facts/dimensions), owned by data teams — ask for a governed view, not raw tables.
- **CMDB:** configuration items (services, servers, apps) and their relationships — key context for incident triage (M14).
- **Document stores, SharePoint/Confluence:** usually via RAG (M03).
- Practicalities: **connection pooling**, credential rotation (Secrets Manager), network path (VPC, VPN/Direct Connect to on-prem), firewall rules, query cost and load on production systems.

---

## Self-check (try first, then open)
<details><summary>How do you let an agent query a production database safely?</summary>

Never the primary with app credentials. Use a read replica or analytics copy; a dedicated read-only role limited to curated views/columns (no PII unless required), row-level security if multi-tenant, statement timeout and row limits; SQL validated by a parser (single SELECT, allow-listed objects, enforced LIMIT); credentials from Secrets Manager; network access only from the agent's subnet; query logging and alerting; and evaluation with tricky and malicious questions before go-live.
</details>

<details><summary>What breaks when many Lambda invocations open database connections at once?</summary>

Each concurrent Lambda environment opens its own connection(s); a traffic burst can exhaust the database's `max_connections` and memory, causing connection errors and latency for everyone (including other apps). Fixes: RDS Proxy (pooling/multiplexing), reuse connections across invocations (init outside the handler), cap Lambda reserved concurrency, use the Data API, or queue work via SQS.
</details>

## Resources
- PostgreSQL docs: window functions, `EXPLAIN`, transaction isolation, row-level security, `GRANT`
- `sqlglot` documentation
- Amazon RDS Proxy; DynamoDB best practices (single-table design); Athena performance tuning
- Practice: pgexercises.com, SQLBolt; LeetCode database problems

**Next:** [Lab environment setup](../labs/SETUP.md) → [Lab 01](../labs/lab-01-text-to-sql-safe/README.md)
