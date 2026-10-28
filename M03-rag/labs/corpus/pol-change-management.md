---
title: Change management policy
type: policy
service: process
updated: 2026-03-03
allowed_groups: [it-ops]
---
# Change management policy

Every change to a production system needs a change record (CHG number) before work starts.

## Change types
| Type | Example | Approval | Lead time |
|---|---|---|---|
| Standard | pre-approved, low-risk, repeatable (certificate renewal using the runbook, adding a user to a group) | none; use the template | none |
| Normal | anything else: releases, configuration changes, firewall rules | Change Advisory Board (CAB), Tuesdays 15:00 IST | 5 working days |
| Emergency | needed to restore service during an incident | incident commander, reviewed at the next CAB | none |

## Change freeze
- **Month-end close**: the last 2 working days of each month and the first 3 working days of the next. No normal changes to ERP, finance systems or the orders database.
- **Year-end freeze**: 15 December to 5 January for all production systems.
- Additional freezes can be declared for a single system, for example during a rollback (CHG0004321 froze the ERP application tier in June 2026).

## Every change record states
- what changes, on which systems, and the exact steps;
- how to test that it worked;
- how to roll back, and how long rollback takes;
- the expected user impact and who has been told.

Failed or rolled-back changes are reviewed at the next CAB.
