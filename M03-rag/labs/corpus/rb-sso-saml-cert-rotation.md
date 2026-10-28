---
title: Rotate the SAML signing certificate
type: runbook
service: sso
updated: 2026-04-29
allowed_groups: [it-ops]
---
# Rotate the SAML signing certificate

The IdP signs SAML assertions with a certificate that is valid for 2 years. About 40 connected applications trust it, including the ERP, Salesforce and the expense tool. Rotating it badly logs everyone out of those apps.

## Overlap rotation (the only allowed method)
1. Six weeks before expiry, generate the new certificate and publish it as the **secondary** signing certificate in the IdP metadata.
2. Email the owners of every connected app with the metadata URL. Apps that import metadata automatically pick it up within 24 hours.
3. Track each app in the rotation sheet until its owner confirms the new certificate is trusted.
4. On the switch date, make the new certificate primary. Keep the old one as secondary for 7 days.
5. Remove the old certificate.

## Lessons from INC0010388
In April 2026 the certificate expired because nobody owned the rotation sheet. ERP and expenses were unavailable for 3 hours. The rotation now has a named owner in the change calendar.
