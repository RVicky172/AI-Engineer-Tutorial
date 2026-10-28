---
title: "INC0011140: No Wi-Fi on floor 5"
type: incident
service: wifi
updated: 2026-07-18
allowed_groups: [it-ops]
---
# INC0011140: No Wi-Fi on floor 5

**Priority:** P1 · **Duration:** 1 h 35 min · **Users affected:** about 60

## Summary
On 16 July 2026 from 09:20 IST, laptops on floor 5 connected to `ACME-Corp` but got no IP address ("No internet, secured"). Other floors were fine.

## Root cause
The marketing team moved to floor 5 the day before, and the floor's DHCP scope (a /25, 126 addresses) was exhausted by laptops, phones and 40 new IoT displays that should have been on the `ACME-IoT` VLAN. The DHCP lease time of 8 days meant addresses from the move day were never released.

## Resolution
The engineer first rebooted the Wi-Fi controller, which did not help and disconnected the other floors for 2 minutes. At 10:40 the scope was extended to a /24 and the displays moved to `ACME-IoT`; clients recovered by 10:55.

## Actions
1. DHCP scope utilisation above 85% now raises an alert.
2. Lease time on office VLANs reduced to 8 hours.
3. The Wi-Fi controller runbook now starts with "check DHCP and PoE before rebooting".
4. Facilities moves now include an IT checklist item for new devices.
