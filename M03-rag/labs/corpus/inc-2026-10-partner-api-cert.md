---
title: "INC0012120: Partner API certificate expired"
type: incident
service: security
updated: 2026-10-10
allowed_groups: [it-ops]
---
# INC0012120: Partner API certificate expired

**Priority:** P1 · **Duration:** 1 h 50 min · **Impact:** distributors could not submit orders through `partner-api.acme.example`

## Summary
On 6 October 2026 at 00:00 UTC the TLS certificate of the partner API expired. Partner systems rejected the connection; orders through the API stopped. The web shop was not affected.

## Root cause
The partner API had been moved to a new load balancer in May with a manually imported certificate instead of an ACM-managed one. The endpoint was never added to `cert-inventory.yaml`, so the weekly expiry check did not see it.

## Resolution
An ACM certificate was requested and attached to the load balancer; DNS validation completed in 25 minutes.

## Actions
1. All public endpoints use ACM-managed certificates with automatic renewal.
2. New endpoints must be added to the certificate inventory in the same change that creates them.
3. The certificate monitor now also scans every listener on our AWS load balancers.
