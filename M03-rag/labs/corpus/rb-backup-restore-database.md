---
title: Restore the orders database to a point in time
type: runbook
service: database
updated: 2026-06-30
allowed_groups: [it-ops]
---
# Restore the orders database to a point in time

RDS keeps automated backups of `orders-db-prod` for **14 days** and supports point-in-time restore to any second in that window. Manual snapshots before releases are kept for 90 days.

## Steps
1. Get approval from the data platform lead; a restore is a normal change unless it is part of an incident.
2. `aws rds restore-db-instance-to-point-in-time --source-db-instance-identifier orders-db-prod --target-db-instance-identifier orders-db-restore-<date> --restore-time <UTC time>`
3. The restore creates a **new** instance; it never overwrites production. Restores take 20-60 minutes.
4. Copy the needed rows back with a reviewed SQL script, or point applications at the new instance during an incident.
5. Delete the restored instance when done; it is billed per hour.
