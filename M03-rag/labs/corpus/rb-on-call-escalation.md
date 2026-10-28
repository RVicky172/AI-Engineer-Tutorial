---
title: On-call escalation paths
type: runbook
service: process
updated: 2026-10-01
allowed_groups: [it-ops]
---
# On-call escalation paths

Page through the paging tool, not by phone, so the page is logged. Phone only if a page is not acknowledged.

| Service | First line (on-call rota) | Escalate to after 15 min | Vendor |
|---|---|---|---|
| VPN, Wi-Fi, LAN | network on-call | network lead | gateway vendor TAC, contract NW-7781 |
| SSO, MFA | identity on-call | IAM lead | none |
| ERP | erp-support on-call | ERP platform manager | ERP vendor support, priority line, contract ERP-2290 |
| Orders database | DBA on-call | data platform lead | AWS Support (Business) |
| Kubernetes (prod-eks-1) | platform on-call | platform lead | AWS Support (Business) |
| Email relay | messaging on-call | infrastructure lead | smart host provider |
| Security incidents | security on-call | CISO | incident response retainer, contract SEC-0042 |

## Rules
- The duty manager is paged automatically for every P1.
- A P1 that has had no acknowledged owner for 15 minutes escalates to the head of IT operations automatically.
- Out of hours, P3 and P4 tickets wait for business hours. Do not page for them.
- AWS Support cases for production are opened with severity "Production system down" only for P1s.
