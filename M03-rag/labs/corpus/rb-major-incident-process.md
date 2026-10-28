---
title: Major incident process
type: runbook
service: process
updated: 2026-09-01
allowed_groups: [it-ops]
---
# Major incident process

A major incident is any P1, or a P2 that is not under control after 60 minutes. This process overrides normal ticket handling: speed and communication come first, root cause later.

## Roles
| Role | Who | Responsibilities |
|---|---|---|
| Incident commander (IC) | the on-call duty manager | owns the incident, makes decisions, assigns tasks, decides when it is resolved |
| Technical lead | the senior engineer of the affected service | leads diagnosis and the fix, tells the IC what is needed |
| Communications lead | service desk team lead | writes status updates, keeps stakeholders away from the engineers |
| Scribe | anyone available | keeps the timeline in the incident ticket |

One person may hold two roles in a small incident, but the IC should never also be the technical lead: the IC must keep the overview.

## First 15 minutes
1. The service desk or the monitoring alert opens the incident and sets priority using the incident severity policy.
2. The service desk pages the duty manager through the paging tool. The duty manager acknowledges within 5 minutes or the page escalates to the head of IT operations.
3. The IC opens a bridge (Teams meeting "MI-<incident number>") and the Slack channel `#mi-<incident number>`.
4. The IC confirms the impact: which service, how many users, since when, any workaround.
5. The communications lead sends the first status message within 15 minutes of the P1 being declared, even if the cause is unknown.

## Communication cadence
| Priority | Status updates | Audience |
|---|---|---|
| P1 | every 30 minutes | all affected users, IT leadership, business owner |
| P2 | every 60 minutes | affected teams, service owner |

Each update says: what is affected, what we know, what we are doing, when the next update comes. Never promise a fix time you cannot control; give the next update time instead.

## Working the incident
- Prefer restoring service over finding the root cause: fail over, roll back, restart. Keep evidence (logs, screenshots) before restarting things.
- Every change during the incident is announced in the channel before it is made, and recorded by the scribe.
- If a fix needs a change that normally needs CAB approval, the IC can approve an emergency change; record it as such.
- Bring in a vendor early. Waiting two hours to open a vendor case is the most common delay in our postmortems.

## Resolution
1. The IC declares the incident resolved when the service has been stable for 30 minutes.
2. The communications lead sends the resolution message.
3. The IC schedules the postmortem within 5 working days. Postmortems are blameless: they look for system and process causes, not people to blame.
4. Every postmortem action gets an owner and a due date in the problem record.
