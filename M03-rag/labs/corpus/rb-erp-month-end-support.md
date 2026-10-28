---
title: ERP support during month-end close
type: runbook
service: erp
updated: 2026-07-01
allowed_groups: [it-ops]
---
# ERP support during month-end close

Finance closes the books in the last 2 working days of each month and the first 3 of the next. ERP support works an extended shift (07:00-23:00 IST) in that period.

## Daily checks during close
- 07:00: confirm all nightly batch jobs completed (`erp-sched status --date today`).
- 09:00 and 14:00: check `ERP-4012` error counts and database lock waits.
- 18:00: confirm the close timetable with the finance systems lead.

## Escalation
Any ERP P1 or P2 during close is escalated to the ERP platform manager immediately, and the ERP vendor's priority line is used (contract ERP-2290).
