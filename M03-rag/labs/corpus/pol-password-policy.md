---
title: Password and MFA policy
type: policy
service: security
updated: 2026-01-10
allowed_groups: [all-staff]
---
# Password and MFA policy

Applies to every ACME account, including contractors.

## Passwords
- At least 14 characters. A passphrase of four or more words is recommended.
- Passwords do not expire on a schedule. You must change your password immediately if you suspect someone else knows it.
- Not one of your last 10 passwords, and not on the list of known breached passwords (checked automatically).
- Never reuse your ACME password on another website.
- Never share your password, not even with IT or your manager. IT will never ask for it.

## Multi-factor authentication
- MFA is required for every sign-in from outside the office network, and for every sign-in to admin portals.
- Use Microsoft Authenticator with number matching. SMS codes are allowed only as a backup method.
- Never approve an MFA prompt you did not start. Report unexpected prompts to the service desk as a security incident.

## Service accounts
Service accounts use secrets of at least 32 random characters stored in the secrets manager, are rotated every 90 days, and must have a named owner.
