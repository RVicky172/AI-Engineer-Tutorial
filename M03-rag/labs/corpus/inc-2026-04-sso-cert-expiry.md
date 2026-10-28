---
title: "INC0010388: SAML signing certificate expired"
type: incident
service: sso
updated: 2026-04-30
allowed_groups: [it-ops]
---
# INC0010388: SAML signing certificate expired

**Priority:** P1 · **Duration:** 3 h 10 min · **Users affected:** all users of ERP, expenses and 12 other SAML apps

## Summary
On 27 April 2026 at 05:30 IST the IdP's SAML signing certificate expired. Every application that validates SAML assertions rejected logins with "invalid SAML response". Email and Teams (OIDC) were not affected.

## Root cause
The certificate was valid for 2 years. The rotation reminder went to the mailbox of an engineer who had left the company, and the rotation sheet had no owner. The certificate monitor did not cover SAML signing certificates, only TLS endpoints.

## Resolution
A new certificate was generated and published at 06:40. Apps with automatic metadata refresh recovered by 07:30. The ERP and the expense tool needed their metadata re-imported by hand by their vendors, which took until 08:40.

## Actions
1. The SAML rotation runbook now requires an overlap rotation starting six weeks before expiry.
2. The rotation has a named owner (IAM lead) in the change calendar.
3. SAML signing certificates were added to the certificate monitor.
4. Every SAML app owner must support metadata URL refresh by the end of 2026.
