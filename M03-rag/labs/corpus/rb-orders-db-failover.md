---
title: Fail over the orders database
type: runbook
service: database
updated: 2026-06-30
allowed_groups: [it-ops]
---
# Fail over the orders database

The web shop's orders database is PostgreSQL 16 on Amazon RDS (`orders-db-prod`), Multi-AZ, with one read replica `orders-db-replica-1` used for reporting.

## Automatic failover
RDS fails over to the standby automatically when the primary's host or AZ fails. It usually takes 60-120 seconds. The DNS endpoint `orders-db-prod.cluster.acme.example` does not change, but applications must reconnect. The web shop's connection pool (HikariCP) reconnects on its own; the reporting jobs do not and must be restarted.

## Manual failover (forced)
Use only when the primary is degraded but RDS has not failed over (for example storage latency above 200 ms for 10 minutes):
1. Raise or link a P1. Manual failover drops every connection.
2. `aws rds reboot-db-instance --db-instance-identifier orders-db-prod --force-failover`
3. Watch `DatabaseConnections` and `WriteLatency` in CloudWatch.
4. Run the checkout smoke test `make smoke-checkout` from the `shop-ops` repo.

## After any failover
- Check replication lag on `orders-db-replica-1` (`ReplicaLag` below 30 s).
- Restart the reporting service: `kubectl -n reporting rollout restart deploy/report-api`.
- Record the failover time in the incident.

Do not promote the read replica. It is not sized for production writes and promoting it breaks replication permanently.
