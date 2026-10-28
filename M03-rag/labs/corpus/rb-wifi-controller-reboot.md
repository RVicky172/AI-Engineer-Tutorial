---
title: Reboot the Wi-Fi controller
type: runbook
service: wifi
updated: 2026-07-19
allowed_groups: [it-ops]
---
# Reboot the Wi-Fi controller

All office access points are managed by the wireless controller `wlc-01` (HA pair with `wlc-02`). SSIDs: `ACME-Corp` (802.1X with the laptop certificate), `ACME-Guest` (captive portal) and `ACME-IoT` (scanners and printers).

## Before rebooting
Most floor-wide outages are not the controller. Check first:
1. Is only one floor affected? Then it is usually the floor switch or its PoE budget. Check `show power inline` on the floor switch; access points drop when PoE is exhausted.
2. Are clients connecting but getting no IP address? Check the DHCP scope for that VLAN (scope exhaustion caused the July 2026 floor 5 outage).
3. Is `ACME-Corp` failing but `ACME-Guest` working? Then RADIUS (the NPS servers) is the problem, not Wi-Fi.

## Reboot
1. Fail over to the standby: `redundancy force-switchover` on wlc-01. Access points rejoin wlc-02 within 2 minutes.
2. Reboot wlc-01 from the console.
3. When it is back, leave wlc-02 active; do not switch back during business hours.
