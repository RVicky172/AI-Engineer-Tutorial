---
title: Restore files from the file server backup
type: runbook
service: storage
updated: 2026-09-12
allowed_groups: [it-ops]
---
# Restore files from the file server backup

The departmental file shares (`\\fs-01\finance`, `\\fs-01\hr`, `\\fs-01\projects`) are backed up with AWS Backup:

| Backup | Frequency | Kept for |
|---|---|---|
| Snapshot | every 4 hours | 7 days |
| Daily | 23:00 IST | 35 days |
| Monthly | 1st of the month | 12 months |

Users can restore their own files from snapshots of the last 7 days with "Previous Versions" in Windows Explorer. Use this runbook for anything older, or for whole folders.

## Steps
1. Get approval from the data owner of the share in the ticket. HR and finance shares need the owner's written approval; IT staff may not browse them.
2. In AWS Backup, find the recovery point closest to (and before) the requested time.
3. Restore to a **new** volume, never over the live one. Mount it on the restore host `fs-restore-01`.
4. Copy only the requested files back to a `Restored-<date>` folder in the share, so nothing in use is overwritten.
5. Detach and delete the restored volume within 48 hours; it is billed per GB.

The September 2026 backup incident showed that a failed daily backup is only visible in the AWS Backup console: check the weekly backup report every Monday.
