---
title: "INC0010702: ERP invoices and password reset emails delayed"
type: incident
service: email
updated: 2026-05-31
allowed_groups: [it-ops]
---
# INC0010702: ERP invoices and password reset emails delayed

**Priority:** P2 · **Duration:** 5 h · **Impact:** customer invoices delayed; password reset emails arrived up to 4 hours late

## Summary
On 29 May 2026 the month-end ERP invoice run sent 38,000 emails in 20 minutes through `mail-relay-01`. The smart host provider throttled our account to 50 messages per minute. The Postfix queue peaked at 31,000 messages.

## What made it worse
The on-call engineer flushed the queue (`postqueue -f`) several times. Each flush sent a burst that extended the throttling window. Password reset emails waited in the same queue as invoices.

## Resolution
Flushing stopped at 14:10; the queue drained by 18:30 as the provider lifted throttling.

## Actions
1. The ERP invoice run now sends in batches of 2,000 per 10 minutes.
2. Password reset emails use a separate transport with priority (`transport_maps`), so they never wait behind bulk mail.
3. The mail relay runbook says: do not flush repeatedly when upstream throttles.
4. Raised the provider rate limit to 500 messages per minute (contract change).
