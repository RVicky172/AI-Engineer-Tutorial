---
title: "INC0008820: VPN certificate expired on the standby gateway"
type: incident
service: vpn
updated: 2025-11-20
allowed_groups: [it-ops]
---
# INC0008820: VPN certificate expired on the standby gateway

**Priority:** P2 · **Duration:** 1 h 10 min

During planned maintenance on 15 November 2025, the VPN was failed over to the Mumbai gateway. Every client failed with `VPN-ERR-820 certificate expired`: the certificate had been renewed on the primary in October but not on the standby.

The failover was reverted, the certificate installed on the standby, and the maintenance repeated the next weekend.

Action: the renewal runbook now requires installing the certificate on both gateways.
