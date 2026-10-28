---
title: VPN failover procedure (2024, superseded)
type: runbook
service: vpn
updated: 2024-06-10
status: superseded
allowed_groups: [it-ops]
---
# VPN failover procedure (2024, superseded)

> Superseded: the gateways were replaced in 2025. Use "Fail over the VPN to the backup gateway".

The old VPN pair `vpn-a` (Pune) and `vpn-b` (Pune, second rack) shared a virtual IP with VRRP. Failover was automatic; manual failover was done with `vrrp priority 50` on vpn-a.

The backup unit was licensed for 1,000 concurrent users. Above that, users saw "maximum sessions reached". Both units were in the same data centre, so a site outage took down both.
