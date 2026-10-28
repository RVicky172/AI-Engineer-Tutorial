---
title: Re-run a failed ERP batch job
type: runbook
service: erp
updated: 2026-07-21
allowed_groups: [it-ops]
---
# Re-run a failed ERP batch job

Nightly ERP batch jobs run in the scheduler `erp-sched` between 01:00 and 05:00 IST. The important ones:

| Job | Runs at | What it does | Safe to re-run? |
|---|---|---|---|
| `FIN_GL_POST` | 01:00 | posts the day's journals to the general ledger | only after checking for partial posts |
| `AP_INVOICE_IMPORT` | 02:00 | imports supplier invoices from the OCR system | yes, it skips duplicates |
| `AR_DUNNING` | 03:00 | sends payment reminders to customers | **no**: customers get duplicate reminders |
| `INV_VALUATION` | 04:00 | recalculates stock value | yes |

## Steps
1. Find the failure: `erp-sched status --date today --failed`.
2. Read the job log in `/var/log/erp/batch/<JOB>_<date>.log`. Lock timeouts (`ORA-00060 deadlock`) usually mean a user session held a lock overnight.
3. For `FIN_GL_POST`, run the partial-post check `FIN_GL_CHECK --date <date>` first. If it reports partial journals, call the finance systems team; never re-run on top of a partial post.
4. Re-run: `erp-sched run <JOB> --date <date>`.
5. Note the re-run in the incident ticket with the job log path.

A re-run during business hours slows invoice posting for everyone. Before 08:00 IST is fine; after that, get approval from the finance systems lead.
