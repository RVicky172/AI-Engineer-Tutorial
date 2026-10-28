---
title: "INC0010231: VPN outage for Pune office users"
type: incident
service: vpn
updated: 2026-03-19
allowed_groups: [it-ops]
---
# INC0010231: VPN outage for Pune office users

**Priority:** P1 · **Duration:** 2 h 05 min · **Users affected:** about 600 remote users

## Summary
On 17 March 2026 from 08:52 to 10:57 IST, remote users could not connect to the VPN and saw `VPN-ERR-809 gateway unreachable`. The primary gateway `vpn-gw-02` had crashed after a memory leak in firmware 9.1.3.

## Timeline
- 08:52 health checks on vpn-gw-02 start failing.
- 09:05 first user calls; the service desk treats them as individual problems.
- 09:40 the service desk notices 30+ calls and declares a P1.
- 09:55 the network on-call tries to restart vpn-gw-02; it crashes again within minutes.
- 10:30 decision to fail over to vpn-gw-01; DNS changed at 10:42.
- 10:57 sessions on vpn-gw-01 back to normal levels.

## Root cause
Firmware 9.1.3 leaked memory on every TLS renegotiation. After 41 days of uptime the gateway ran out of memory. The standby had a different firmware version and was not affected.

## What went well / badly
- Failover worked once started, but started too late: the runbook did not say when to fail over instead of restarting.
- The monitoring alert on vpn-gw-02 went to an email folder nobody watched.

## Actions
1. Upgrade both gateways to firmware 9.1.5 (done 2026-03-24).
2. Runbook updated: fail over when health checks fail for more than 3 minutes; restart later.
3. Gateway alerts now page the network on-call.
4. Service desk: 5 or more calls about the same service in 15 minutes trigger a major incident check.
