---
title: Security incident response playbook
type: security
service: security
updated: 2026-08-30
allowed_groups: [security]
---
# Security incident response playbook

Used by the security on-call for every suspected compromise: phishing with credentials entered, malware, lost devices with unencrypted data, data sent to the wrong party, and unusual sign-ins.

## 1. Triage (first 15 minutes)
- Confirm what happened and when, which accounts and devices are involved, and whether data left the company.
- Classify: credential compromise, malware, data leak, insider, or other.
- Open a P1 security incident; it is restricted to the security group.

## 2. Contain
| Situation | Containment |
|---|---|
| Credentials entered on a phishing page | reset password, revoke all sessions and refresh tokens, check MFA methods for attacker-added devices |
| Malware executed | isolate the device with the EDR console (network containment), do not power it off |
| Mailbox compromise | remove inbox rules and forwarding, search sent items for further phishing |
| Lost device | remote lock and wipe through Intune, revoke sessions |

## 3. Investigate
Collect sign-in logs (90 days), EDR timeline, mailbox audit log and proxy logs. Preserve evidence before cleaning devices: memory image for malware cases.

## 4. Notify
- Personal data affected: inform the data protection officer within 24 hours; regulators may need notification within 72 hours.
- Engage the incident response retainer (contract SEC-0042) for anything beyond one compromised account.

## 5. Recover and learn
Restore from known-good backups, re-enable accounts only after the root cause is understood, and hold a postmortem within 5 working days.
