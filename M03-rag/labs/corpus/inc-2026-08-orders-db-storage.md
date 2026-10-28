---
title: "INC0011320: Orders database storage full from an inactive replication slot"
type: incident
service: database
updated: 2026-08-07
allowed_groups: [it-ops]
---
# INC0011320: Orders database storage full from an inactive replication slot

**Priority:** P1 · **Duration:** 1 h 15 min · **Impact:** web shop checkout read-only; no new orders for 38 minutes

## Summary
On 4 August 2026 `orders-db-prod` reached its 2 TB storage autoscaling maximum. PostgreSQL stopped accepting writes.

## Root cause
A logical replication slot `cdc_orders_v1`, created for a data platform pilot that ended in June, was left behind. An inactive slot prevents PostgreSQL from removing old WAL files, so WAL grew by about 40 GB per day for two months. The `FreeStorageSpace` alert fired, but autoscaling kept adding storage, so the on-call engineer assumed it was normal growth.

## Resolution
After the data platform team confirmed the pilot was over, the slot was dropped (`pg_drop_replication_slot('cdc_orders_v1')`). WAL was recycled within minutes and writes resumed.

## Actions
1. Alert on `OldestReplicationSlotLag` above 10 GB.
2. Replication slots must be created through a change and have an owner and an end date.
3. The storage runbook now checks replication slots first.
