---
title: "VPN error VPN-ERR-809: gateway unreachable"
type: kb
service: vpn
updated: 2026-07-03
allowed_groups: [all-staff]
---
# VPN error VPN-ERR-809: gateway unreachable

The VPN client cannot reach `vpn.acme.example`.

## Check your own connection first
1. Can you open a public website? If not, the problem is your home or hotel internet.
2. Hotel and airport Wi-Fi often block VPN traffic until you accept the portal terms. Open a browser and accept them, then reconnect.
3. If you are on a phone hotspot, check you have mobile data left.

## Try the backup gateway
In the VPN client, open **Settings → Gateway** and pick `vpn-backup.acme.example` (the Mumbai gateway). Reconnect. The backup gateway has fewer licences, so switch back to **Automatic** the next day.

## Still failing?
If colleagues get the same error, it is probably an outage: check the IT status page `https://status.acme.example` before calling. If the status page is green, call the service desk on extension 4357 with the time of the error and your public IP address (from `https://ifconfig.acme.example`).

Related errors: `VPN-ERR-812` means all licences are in use; try again in 15 minutes. `VPN-ERR-820` means the gateway certificate has expired; this is always an IT problem, report it.
