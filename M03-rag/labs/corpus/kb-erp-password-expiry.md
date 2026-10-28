---
title: ERP says your password has expired
type: kb
service: erp
updated: 2026-04-29
allowed_groups: [all-staff]
---
# ERP says your password has expired

The ERP uses single sign-on: it has no password of its own. If the ERP login page says "password expired" or "invalid SAML response", the problem is your SSO session, not an ERP password.

1. Close all browser windows and open the ERP again from `https://apps.acme.example`.
2. If your SSO password expired, reset it at `https://id.acme.example/reset`.
3. Clear the browser cache for `acme.example` if the error persists.

If everyone gets "invalid SAML response" at the same time, it is an outage of the SSO signing certificate; IT already knows, check `https://status.acme.example`.
