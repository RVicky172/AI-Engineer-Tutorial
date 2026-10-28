---
title: Orders database storage almost full
type: runbook
service: database
updated: 2026-08-05
allowed_groups: [it-ops]
---
# Orders database storage almost full

Alert: `FreeStorageSpace < 10%` on `orders-db-prod`.

RDS storage autoscaling is enabled with a maximum of 2 TB. The alert fires when autoscaling has already reached the maximum, or when growth is faster than autoscaling can follow.

## Diagnose
1. Find the biggest tables: `SELECT relname, pg_size_pretty(pg_total_relation_size(relid)) FROM pg_catalog.pg_statio_user_tables ORDER BY pg_total_relation_size(relid) DESC LIMIT 10;`
2. Check for bloat after a big delete: dead tuples in `pg_stat_user_tables.n_dead_tup`.
3. Check for a stuck replication slot: `SELECT slot_name, active FROM pg_replication_slots;` An inactive slot keeps WAL forever. This caused the August 2026 incident.

## Fix
- Inactive replication slot: drop it (`SELECT pg_drop_replication_slot('name');`) after confirming with the data platform team that nothing uses it.
- Table bloat: schedule `VACUUM (ANALYZE)` on the table; `VACUUM FULL` locks the table and needs a change window.
- Real growth: raise the autoscaling maximum with a change request.
