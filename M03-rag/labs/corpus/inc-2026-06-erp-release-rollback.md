---
title: "INC0011054: ERP release 24.3 rolled back after posting timeouts"
type: incident
service: erp
updated: 2026-06-28
allowed_groups: [it-ops]
---
# INC0011054: ERP release 24.3 rolled back after posting timeouts

**Priority:** P2 · **Duration:** 2 days · **Impact:** invoice posting took 2-3 minutes per document; many `ERP-4012` errors

## Summary
ERP release 24.3 went live on 24 June 2026. It added an index rebuild to the nightly `FIN_GL_POST` job, which then ran until 11:00 instead of 03:00 and held locks on the posting tables during business hours. Accounts payable saw `ERP-4012 Posting timed out` all morning.

## What made it worse
On 25 June an engineer restarted the ERP application tier to "clear the timeouts" while the rollback change CHG0004321 was running. The restart interrupted a posting batch, which had to be repaired by the vendor.

## Resolution
Release 24.3 was rolled back under CHG0004321 on 26 June. A change freeze on the ERP application tier was in place until the rollback was verified.

## Actions
1. The ERP restart runbook now says: check the change calendar; never restart during a freeze or month-end close.
2. ERP releases include a performance test of the nightly batch with production-sized data.
3. `ERP-4012` errors are monitored; more than 50 in 15 minutes pages erp-support.
