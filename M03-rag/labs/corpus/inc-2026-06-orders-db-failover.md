---
title: "INC0010911: Checkout errors after orders database failover"
type: incident
service: database
updated: 2026-06-15
allowed_groups: [it-ops]
---
# INC0010911: Checkout errors after orders database failover

**Priority:** P1 · **Duration:** 47 min · **Impact:** about 2,100 failed checkouts

## Summary
On 12 June 2026 at 20:14 IST, an AZ problem in ap-south-1 caused an automatic Multi-AZ failover of `orders-db-prod`. RDS completed the failover in 95 seconds, but the web shop kept failing checkouts for 47 minutes.

## Root cause
The checkout service cached the database's IP address instead of resolving the endpoint name for each new connection (the JVM DNS cache TTL was set to "forever"). After the failover it kept connecting to the old primary, which was now unreachable. The reporting service had the same problem.

## Resolution
Restarting the checkout pods at 21:01 forced a new DNS lookup.

## Actions
1. Set `networkaddress.cache.ttl=30` for all JVM services.
2. The failover runbook now includes restarting services that do not reconnect, and the checkout smoke test.
3. A quarterly failover test in staging (`aws rds reboot-db-instance --force-failover`) to catch this before production.
