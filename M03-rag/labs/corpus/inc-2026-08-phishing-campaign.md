---
title: "INC0011452: Payslip phishing campaign"
type: incident
service: security
updated: 2026-08-29
allowed_groups: [security]
---
# INC0011452: Payslip phishing campaign

**Priority:** P1 · **Duration:** 9 h · **Accounts compromised:** 3

## Summary
On 26 August 2026, 1,240 employees received an email "Your August payslip is ready" linking to a fake login page on `acme-payroll-portal.example`. 17 users clicked; 3 entered their passwords and approved an MFA push sent by the attacker.

## Detection and response
- 10:12 first user report via the Report Phishing button.
- 10:25 security blocked the domain at the proxy and purged the email from all mailboxes.
- 10:40 the three accounts were identified from sign-in logs (same foreign IP range); passwords reset and sessions revoked by 11:05.
- One compromised account had created an inbox rule forwarding mail to an external address; the rule was removed and the forwarded messages reviewed by legal.

## Root cause
MFA push notifications without number matching let users approve a prompt they did not start ("MFA fatigue").

## Actions
1. Number matching enabled for all MFA push notifications (done 2026-08-27).
2. External auto-forwarding rules blocked tenant-wide.
3. Targeted awareness training for the 17 users who clicked.
4. Phishing simulation themed on payroll every quarter.
