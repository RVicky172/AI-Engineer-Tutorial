---
title: Fail over the VPN to the backup gateway
type: runbook
service: vpn
updated: 2026-07-02
allowed_groups: [it-ops]
---
# Fail over the VPN to the backup gateway

ACME runs two VPN gateways in active/standby: `vpn-gw-02` (primary, Pune DC) and `vpn-gw-01` (standby, Mumbai DC). Clients connect to `vpn.acme.example`, a DNS name with a 60-second TTL that points at the active gateway.

## When to use
- Health checks on `vpn-gw-02` fail for more than 3 minutes, or
- More than 20 users report `VPN-ERR-809 gateway unreachable`, or
- Planned maintenance on the primary.

## Before you start
1. Open or link a P1/P2 incident. Failover without an incident number is not allowed.
2. Check `vpn-gw-01` is healthy: `curl -s https://vpn-gw-01.acme.example/health` must return `{"status":"ok"}`.
3. Confirm the standby licence has enough seats: `show license usage` on vpn-gw-01. It holds 1,500 seats; the primary holds 2,500.

## Steps
1. In the DNS console, change the `vpn.acme.example` A record from `10.20.0.12` (vpn-gw-02) to `10.30.0.12` (vpn-gw-01).
2. Wait two TTLs (2 minutes). New connections go to the standby.
3. Existing sessions on the primary drop when it fails; users reconnect automatically within 30 seconds.
4. Watch the `vpn_active_sessions` dashboard. Sessions on vpn-gw-01 should climb to the usual daytime level (900-1,400).
5. Post in #major-incidents: "VPN failed over to vpn-gw-01 at HH:MM, seats limited to 1,500".

## Rollback
Point the A record back to `10.20.0.12` once vpn-gw-02 has passed health checks for 15 minutes. Do it outside 09:00-11:00 IST, when login volume peaks.

## Known issues
- The standby has 1,500 seats. Above that, users get `VPN-ERR-812 licence exhausted`. Ask non-essential users to disconnect.
- Split tunnelling is configured only on the primary; on the standby all traffic is tunnelled, so video calls are slower.
