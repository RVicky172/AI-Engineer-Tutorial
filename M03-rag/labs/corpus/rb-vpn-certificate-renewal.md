---
title: Renew the VPN gateway TLS certificate
type: runbook
service: vpn
updated: 2026-05-18
allowed_groups: [it-ops]
---
# Renew the VPN gateway TLS certificate

The VPN gateways present a TLS certificate for `vpn.acme.example`, issued by the internal CA "ACME Issuing CA 2". It is valid for 398 days. The certificate monitor alerts 30 days before expiry.

## Steps
1. Generate a CSR on the gateway: `crypto pki generate csr vpn.acme.example` (the key never leaves the device).
2. Submit the CSR in the PKI portal under template `ACME-TLS-Server`. Approval by the security team takes up to 1 working day.
3. Install the issued certificate on **both** gateways (vpn-gw-01 and vpn-gw-02). Forgetting the standby is the most common mistake: a later failover then breaks every client.
4. Reload the TLS profile during a change window: `crypto pki reload profile vpn-tls`. Sessions are not dropped.
5. Verify from outside: `openssl s_client -connect vpn.acme.example:443 | openssl x509 -noout -enddate`.

## If the certificate already expired
Clients show `VPN-ERR-820 certificate expired`. Raise a P1, request an emergency certificate from the security on-call engineer by phone, and install it on both gateways.
