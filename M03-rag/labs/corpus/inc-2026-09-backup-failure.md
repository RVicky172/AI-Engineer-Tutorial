---
title: "INC0011733: File server backups silently failing for 11 days"
type: incident
service: storage
updated: 2026-09-14
allowed_groups: [it-ops]
---
# INC0011733: File server backups silently failing for 11 days

**Priority:** P2 · **Impact:** no daily backups of `\\fs-01` from 1 to 11 September 2026; snapshots still worked

## Summary
A user asked for a file deleted 10 days earlier. The restore failed: no daily recovery point existed after 31 August.

## Root cause
An IAM policy change on 31 August removed the `backup:StartBackupJob` permission from the role used by the backup plan. AWS Backup recorded each failed job, but failures only appear in the AWS Backup console and in EventBridge; nobody subscribed to the failure events.

## Resolution
The permission was restored and a manual backup started on 11 September. The user's file was recovered from the 4-hourly snapshot by luck (it was still within 7 days of a later edit).

## Actions
1. EventBridge rule on `Backup Job State Change` with state `FAILED` now pages the infrastructure on-call.
2. Weekly backup report reviewed every Monday (added to the restore runbook).
3. IAM changes to backup roles require a second reviewer.
