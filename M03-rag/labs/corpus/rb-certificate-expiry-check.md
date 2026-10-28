---
title: Weekly TLS certificate expiry check
type: runbook
service: security
updated: 2026-10-08
allowed_groups: [it-ops]
---
# Weekly TLS certificate expiry check

Every Monday the on-call engineer reviews certificates that expire within 45 days. The certificate monitor scans all hosts listed in `cert-inventory.yaml` and public endpoints.

## Steps
1. Open the "Certificate expiry" dashboard. Anything below 30 days is red.
2. For each red entry, check the owner column and open a change for the renewal.
3. Public certificates (from the public CA) renew automatically through ACM where the endpoint uses an AWS load balancer. Internal certificates (ACME Issuing CA 2) need a manual CSR.
4. Check that the monitor itself ran: the dashboard shows "last scan" and must be less than 24 hours old.

## Known gaps
- Certificates on appliances (VPN gateways, the Wi-Fi controller) are not discovered by the scan; they are tracked by hand in the inventory file.
- The partner API certificate that expired in October 2026 (INC0012120) was missing from the inventory. Every new endpoint must be added in the same change that creates it.
