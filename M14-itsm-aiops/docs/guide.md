# M14 · ITSM, CloudOps, SRE and AIOps Use Cases — Study Guide

> **Priority:** Preferred · **Week:** 8 · **Study time:** ~2-3 h · **Labs:** [../labs](../labs/SETUP.md)

## Why it matters
The job lists ServiceNow and IT-operations use cases as preferred experience. Knowing the domain makes you **faster in customer discovery**: you speak the operations team's language and spot where an agent actually saves time.

## Learning objectives
- Explain ITIL processes and how they relate.
- Navigate ServiceNow's data model and APIs.
- Use SRE concepts (SLIs/SLOs, error budgets, runbooks, postmortems).
- Describe AIOps patterns and where agents fit — and where they must not act alone.
- Quantify the value of an operations agent.

---

## 1. ITIL basics
| Process | What | Example |
|---|---|---|
| **Incident** | unplanned interruption; restore service ASAP | "checkout returns 500s" |
| **Problem** | underlying cause of one or more incidents | "connection pool too small under peak load" |
| **Change** | controlled modification (standard / normal / emergency) with risk assessment and approval (CAB) | "increase pool size, deploy Tuesday" |
| **Request** | standard user request from a catalog | "access to the reporting tool" |
| **Knowledge** | articles/runbooks that speed resolution | "RB-17 Postgres disk full" |
- **Priority = impact × urgency** (P1 critical … P4 low); each priority has **SLAs** (response/resolution times).
- **CMDB:** configuration items (CIs: services, apps, servers, DBs) and their **relationships** (depends on / runs on) — key to impact analysis and routing.
- **Assignment groups** route tickets to the right team.

## 2. ServiceNow concepts
| Concept | Notes |
|---|---|
| Tables | `incident`, `problem`, `change_request`, `sc_req_item`, `kb_knowledge`, `cmdb_ci`, `cmdb_ci_service`, `sys_user`, `sys_user_group` |
| `sys_id` | 32-char unique ID of every record; `number` is the human ID (INC0010001) |
| **REST Table API** | `GET/POST/PATCH/DELETE /api/now/table/{table}` |
| Query params | `sysparm_query` (encoded: `active=true^priority=1^ORDERBYDESCsys_created_on`), `sysparm_fields`, `sysparm_limit`, `sysparm_offset`, `sysparm_display_value=true` |
| Work notes vs. comments | internal vs. visible to the caller |
| Flows (Flow Designer), business rules | server-side automation; can call outbound REST (e.g. to trigger your agent) |
| Catalog items | requestable services with forms and workflows |
| Auth | basic auth (dev), OAuth (production); ACLs on tables/fields |

```bash
curl -s -u "$SN_USER:$SN_PASS" -H "Accept: application/json" \
  "$SN_URL/api/now/table/incident?sysparm_query=active=true^priority=1&sysparm_fields=number,short_description,cmdb_ci,assignment_group&sysparm_limit=5"
```

## 3. SRE concepts
- **SLI:** measured indicator (e.g. % of requests < 500 ms and non-5xx).
- **SLO:** target for an SLI (99.9% over 30 days).
- **Error budget:** 100% − SLO; when spent, prioritise reliability over features.
- **Runbooks:** step-by-step responses to known alerts — ideal RAG source and automation candidates.
- **On-call** and escalation policies; **blameless post-incident reviews** with action items.
- Toil: manual, repetitive, automatable work — the primary target for agents.

## 4. AIOps patterns and where agents fit
| Pattern | Agent role | Autonomy |
|---|---|---|
| **Alert correlation / dedup** | group related alerts into one incident | automatic |
| **Automated triage** | categorise, set priority suggestion, route to group, enrich with CMDB + recent changes | automatic (suggest priority; humans own P1 declaration) |
| **Knowledge suggestions** | find runbooks/similar resolved incidents | automatic |
| **Root-cause suggestions** | hypothesise from logs/metrics/changes, with evidence | suggest only |
| **Auto-remediation** | restart, scale, clear cache, roll back | **approval required** (or pre-approved standard changes with tight guardrails) |
| **Summaries** | shift handover, incident timeline, postmortem draft | automatic, human-reviewed |

Rule of thumb: **read, enrich, summarise, suggest → automatic. Change production state → approval** (unless a narrow, reversible, pre-approved standard change with monitoring and auto-rollback).

## 5. Measuring value
| Metric | How |
|---|---|
| MTTA / MTTR | before vs. after for incidents the agent handled |
| Triage accuracy | % correct category/group/priority vs. human final values |
| Reassignment rate | fewer tickets bounced between groups |
| Analyst time saved | minutes saved per incident × volume × loaded cost |
| Auto-resolved share | % resolved with no human work (with quality checks) |
| Cost per resolved incident | model + infra cost ÷ incidents |
| Quality & safety | wrong-action rate (should be ~0), escalations, user satisfaction |
Agree on a baseline **before** the pilot.

---

## Self-check (try first, then open)
<details><summary>Which incident actions should an agent do automatically and which need approval?</summary>

Automatic: read and enrich (CMDB, recent changes, metrics), deduplicate/correlate, suggest category/priority/group, find runbooks and similar incidents, draft work notes and summaries. Approval: anything that changes production or customer-visible state — restarts, scaling, config changes, rollbacks, closing/resolving incidents, customer communications, changing priority of P1s. Exceptions only for narrow, reversible, pre-approved standard changes with monitoring and audit.
</details>

<details><summary>How would you measure the value of an incident-triage agent to a customer?</summary>

Agree baseline metrics before the pilot (MTTA, MTTR, reassignment rate, analyst minutes per ticket, volume). During the pilot measure triage accuracy against final human values, time saved per incident, reassignments avoided, share auto-resolved, and wrong-action rate; translate time saved × volume × cost into money; subtract run cost (cost per resolved incident); include qualitative feedback from analysts.
</details>

## Resources
- ITIL 4 Foundation overview (Axelos) — incident, problem, change practices
- ServiceNow Developer site: REST Table API, Personal Developer Instance, Flow Designer
- Google SRE book: SLOs, error budgets, eliminating toil, postmortems
- AWS: CloudWatch alarms → EventBridge integration; AWS Systems Manager Automation runbooks; AWS DevOps Guru

**Next:** [Lab environment setup](../labs/SETUP.md) → [Lab 01](../labs/lab-01-servicenow-seed-incidents/README.md)
