---
title: Data classification policy
type: policy
service: security
updated: 2026-02-01
allowed_groups: [all-staff]
---
# Data classification policy

Every document and data set has one of four classifications. The owner of the data decides the classification; if unsure, use the higher one.

| Class | Examples | Who may access | Sharing outside ACME |
|---|---|---|---|
| Public | marketing website, press releases | anyone | allowed |
| Internal | KB articles, intranet, org chart | all employees and contractors | only under NDA |
| Confidential | contracts, budgets, customer lists, incident reports | named groups with a business need | only with approval of the data owner and an NDA |
| Restricted | salaries, personal data of employees, security test findings, credentials | named individuals | never, except to authorities as required by law |

## Handling rules
- Confidential and Restricted documents must carry their class in the header or file name.
- Restricted data must be encrypted at rest and in transit, and access to it is logged.
- Email Restricted data only inside ACME, with sensitivity label "Restricted".
- Search and AI assistants must apply the same access rules as the source system: a user must never see content through search that they could not open directly.
