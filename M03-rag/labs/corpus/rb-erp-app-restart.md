---
title: Restart the ERP application tier
type: runbook
service: erp
updated: 2026-06-26
allowed_groups: [it-ops]
---
# Restart the ERP application tier

The ERP runs on four application servers (`erp-app-01` to `erp-app-04`) behind the load balancer `erp-lb`, with an Oracle database on `erp-db-01`. Finance uses it for invoices, purchase orders and month-end postings.

## Check the change calendar first
ERP restarts are **blocked during month-end close** (the last 2 working days of the month and the first 3 of the next) and during any active ERP change freeze. During a freeze, escalate to the `erp-support` group instead of restarting. In June 2026 a restart during the CHG0004321 rollback corrupted a posting batch (see the ERP release rollback incident).

## Symptoms that justify a restart
- Error `ERP-5003 session pool exhausted` for many users.
- Heap usage above 95% on an app server for 15 minutes (`erp_jvm_heap_used_pct`).
- An app server failing load balancer health checks while the database is healthy.

## Steps (one server at a time)
1. Drain the server in the load balancer: set `erp-app-0N` to `drain` in `erp-lb`. Wait until active sessions are below 5 (up to 20 minutes).
2. Stop the application: `sudo systemctl stop erp-app`.
3. Start it: `sudo systemctl start erp-app`. Start-up takes 6-8 minutes while caches warm.
4. Check `https://erp-app-0N.acme.example/health` returns `UP`.
5. Re-enable the server in `erp-lb`, then move to the next server.

Never restart all four at once: users lose unsaved work, and cold caches make the first hour very slow.

## When not to restart
`ERP-4012 posting timeout` on invoices is almost always a database lock or a slow batch job, not the app tier. See "ERP invoice posting fails with ERP-4012" and the batch job runbook.
