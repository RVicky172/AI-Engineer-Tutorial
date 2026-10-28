# M15 · Customer-Facing Engineering Skills — Study Guide

> **Priority:** Must have · **Week:** 8 · **Study time:** ~2-3 h · **Labs:** [../labs](../labs/SETUP.md)

## Why it matters
About 20% of the role is direct customer interaction — and the other 80% depends on it: how well you capture requirements, set expectations, and hand over determines whether the engineering lands.

## Learning objectives
- Run a structured technical discovery.
- Plan and run workshops, demos and POCs with clear exit criteria.
- Write documentation customers actually use.
- Lead go-live and hypercare.
- Turn field feedback into useful platform feature requests.
- Communicate trade-offs and say "no" constructively.

---

## 1. Technical discovery
Goal: understand the **business outcome** and the **constraints** before designing anything.

| Area | Example questions |
|---|---|
| Business | What problem, for whom? How is it measured today? What does success look like in 90 days? |
| Users & process | Who uses it? What's the current workflow? Where are the hand-offs and delays? |
| Applications & APIs | Which systems hold the data/actions? APIs available? Rate limits? Sandbox access? |
| Data | Where is it, how fresh, how sensitive, who owns it? Data quality? |
| Identity | Which IdP? How are users/groups mapped? Do actions run as the user or a service? |
| Network | Outbound internet allowed? VPCs, VPN/Direct Connect, proxies, private endpoints required? |
| Security & compliance | Data classification, residency, retention, audit, approval for AI use, security review process? |
| Operations | Who runs it after go-live? On-call? Monitoring tools? Change process? |
| Constraints | Timeline, budget, regions, model restrictions, frozen periods? |
Techniques: open questions, then confirm by playing back ("so what I'm hearing is…"); capture **assumptions and risks** explicitly; identify decision makers and blockers (security team!) early.

## 2. Workshops, demos and POCs
- **Workshop:** agenda + desired outputs (e.g. agreed architecture, prioritised use cases), right people in the room, notes sent within 24 h.
- **Demo:** start from the customer's problem, show the workflow end to end with their data shape, show a failure being handled (approval, trace), keep architecture slides plain.
- **POC:** scope written down — use cases, data, integrations, **exit criteria** (measurable: "≥80% correct triage on 50 historical incidents, p95 < 10 s, security review passed"), timeline, owners, what's out of scope.
- **Managing scope:** a change log; new asks go to a backlog with impact on timeline stated.

## 3. Documentation customers use
| Doc | Contents |
|---|---|
| Architecture note | diagram, components, data flow, security boundaries, decisions + alternatives |
| Integration spec | per system: purpose, endpoints, auth, limits, error handling, owner |
| Deployment guide | prerequisites, steps, config, verification |
| Runbook | health checks, alerts → actions, rollback, escalation |
| Troubleshooting guide | symptom → likely cause → checks → fix |
| Knowledge transfer | sessions, recordings, hands-on exercises for the customer team |
Write for the reader: short, skimmable, tested by someone who didn't build it.

## 4. Go-live and hypercare
**Readiness checklist:** evals pass thresholds; security review approved; IAM and network reviewed; monitoring, alarms and on-call in place; rollback tested; data-handling sign-off; UAT signed; support and escalation paths agreed; communication plan.

**Hypercare (first 2-4 weeks):** daily check of dashboards and quality signals, daily short status (what happened, issues, actions, risks), fast fix cycle, clear exit criteria for handing over to steady-state support.

## 5. Feedback loops into the platform
When several customers need the same thing, turn it into a structured request: problem statement, customers affected, current workaround and its cost, proposed capability, evidence (tickets, quotes, metrics), priority. This "architecture contribution" (~10% of the role) is how field work improves the product.

## 6. Communication under pressure
- **Saying no without damage:** acknowledge the goal → explain the impact (timeline/risk) with facts → offer options (phase 2, a simpler version, swap for another item) → let them choose → write it down.
- **Bad news early:** state the issue, impact, what you're doing, when the next update is.
- **Plain language:** explain trade-offs in business terms (risk, time, cost), not jargon.

---

## Self-check (try first, then open)
<details><summary>A customer blocks outbound internet access. How does that change your design?</summary>

Everything must be reachable privately: VPC interface endpoints (PrivateLink) for Bedrock Runtime, AgentCore, Secrets Manager, STS, CloudWatch Logs, ECR (api + dkr) and S3 gateway endpoint; no public package downloads at runtime (bake dependencies into images, use CodeArtifact / private mirrors); third-party SaaS APIs need private connectivity, a controlled egress proxy with allow-list, or are out of scope; private DNS; endpoint policies. Confirm which AWS services/features support private endpoints in their region early — it can change scope and timeline.
</details>

<details><summary>How do you say no to a request that risks the timeline without damaging the relationship?</summary>

Show you understand why they want it, quantify the impact on timeline/risk, and offer options: defer to a later phase, a smaller version now, or swap it for something of equal size — and let the customer's decision maker choose. Document the decision and keep the relationship on shared goals (a successful go-live) rather than on "no".
</details>

## Resources
- AWS Well-Architected Framework (use the pillars to structure discovery questions)
- "The Trusted Advisor" (Maister, Green, Galford) — customer relationships
- "Docs for Developers" (Bhatti et al.) — technical writing
- Google SRE book: launch coordination checklist
- Your own capstone: [../../capstone/README.md](../../capstone/README.md)

**Next:** [Lab environment setup](../labs/SETUP.md) → [Lab 01](../labs/lab-01-discovery-checklist/README.md)
