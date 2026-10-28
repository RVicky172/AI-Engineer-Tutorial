---
title: VPN is slow or video calls stutter on VPN
type: kb
service: vpn
updated: 2026-05-09
allowed_groups: [all-staff]
---
# VPN is slow or video calls stutter on VPN

With **split tunnelling**, only traffic to company systems goes through the VPN; Teams, Zoom and public websites go directly to the internet. This keeps video calls fast.

## Check
1. Open the VPN client and look at **Status → Tunnel mode**. It should say "Split".
2. If it says "Full", you are probably connected to the backup gateway, which tunnels all traffic. Switch **Settings → Gateway** back to **Automatic** and reconnect.

## Other causes
- Your home internet upload speed is below 5 Mbit/s. Test at a speed test site with the VPN off.
- Many devices at home are streaming at the same time.
- Wi-Fi far from the router: use a cable for important calls.

If the VPN is slow for everyone in your office at the same time, report it to the service desk; it may be an outage.
