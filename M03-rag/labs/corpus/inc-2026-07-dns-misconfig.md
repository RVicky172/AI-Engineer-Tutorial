---
title: "INC0011207: Intranet unreachable after DNS change"
type: incident
service: network
updated: 2026-07-28
allowed_groups: [it-ops]
---
# INC0011207: Intranet unreachable after DNS change

**Priority:** P2 · **Duration:** 6 h 20 min · **Impact:** intranet and the status page unreachable from the office network

## Summary
On 24 July 2026 a change moved the intranet to a new load balancer. The CNAME `intranet.acme.example` was updated to point at the new load balancer, but with a typo in the target. The record had a TTL of 24 hours.

## Root cause
The typo was fixed 40 minutes after the change, but the internal resolvers `dns-01` and `dns-02` had cached the broken answer (NXDOMAIN for the target) and kept serving it. Nobody flushed the resolver caches because the runbook did not exist yet.

## Resolution
After escalation to the network lead, `rndc flushname intranet.acme.example` on both resolvers fixed it at 16:20.

## Actions
1. New runbook: "Flush the internal DNS resolver cache".
2. Lower TTLs to 5 minutes for 24 hours before any planned DNS change.
3. DNS changes are peer reviewed in the change record, with the exact record text.
