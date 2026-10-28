# M11 · Testing and Evaluation of Agentic Systems — Study Guide

> **Priority:** Must have · **Week:** 7 · **Study time:** ~3 h · **Labs:** [../labs](../labs/SETUP.md)

## Why it matters
The job description lists functional, integration, security, performance, resiliency, evaluation and UAT testing before rollout. Agents are **non-deterministic**, so "it worked when I tried it" is not evidence. You need numbers that show a change made things better.

## Learning objectives
- Apply a test pyramid to agents.
- Build golden datasets and scenario suites; gate CI on them.
- Use LLM-as-judge responsibly and know its biases.
- Choose metrics for quality, safety, latency and cost.
- Run load, resiliency and security tests.

---

## 1. Test pyramid for agents
```
           ▲  UAT / end-to-end with real users & systems   (few, slow, high confidence)
          ▲▲  Scenario tests: agent behaviour on realistic tasks, mocked tools
         ▲▲▲  Contract / integration tests: tools vs. real or recorded APIs
        ▲▲▲▲  Unit tests: tool functions, parsers, validators, prompt builders (many, fast, deterministic)
```
- **Unit:** pure code — no model calls. Error mapping, schema validation, approval gate logic.
- **Contract:** your tool wrappers vs. the API (OpenAPI validation, recorded fixtures, sandbox instances).
- **Scenario:** run the real model with **mocked tools** that return scripted results and **record** calls. Assert on tool choices, forbidden actions and the final answer.
- **End-to-end / UAT:** real integrations in staging; business users sign off against acceptance criteria.

## 2. Evaluation datasets
- **Golden dataset:** representative inputs + expected outputs/criteria. Sources: real tickets (anonymised), SME-written cases, past failures. Include easy, hard, ambiguous, adversarial and "should refuse/escalate" cases.
- Every production bug becomes a new test case.
- Keep it versioned in git with the prompts.

Scenario example:
```yaml
- id: db-disk-full-01
  input: "INC0000123: orders-db write errors since 09:10"
  mocks:
    get_service_status: {status: degraded, disk_used_pct: 99}
    search_kb: [{doc_id: RB-17, title: "Postgres disk full runbook"}]
  expect:
    tools_called: [get_service_status, search_kb]
    tools_forbidden: [restart_service]        # must not restart a DB with a full disk
    answer_contains: ["RB-17", "disk"]
```

## 3. Metrics
| Category | Metric |
|---|---|
| Task | task success rate, partial success, escalation correctness |
| Tools | tool-selection accuracy, argument validity, unnecessary calls |
| RAG | recall@k, groundedness/faithfulness, citation correctness |
| Safety | policy violations, injection success rate, PII leaks |
| Efficiency | latency p50/p95, steps per task, tokens and cost per task |

**Non-determinism:** run each case N times (e.g. 3-5), report mean and variance; flag flaky cases. Compare against a **baseline** stored in the repo; gate CI on the delta (e.g. fail if success drops > 5 points), not on perfection.

## 4. LLM-as-judge
Use a model to grade outputs against a rubric when exact matching is impossible.
- **Rubric design:** few, specific criteria; anchored scales (what a 1, 3, 5 look like); a reference answer; ask for brief reasoning *then* a structured score.
- **Known biases:** verbosity (longer = better), position (first option preferred), self-preference (same model family), leniency, sensitivity to phrasing; weak on facts it doesn't know.
- **Calibrate** against human scores (agreement %, Cohen's kappa) before trusting it; re-check when you change the judge model or rubric.
- Prefer **deterministic checks** where possible (schema valid, tool called, contains ID) — use the judge only for the remainder.

## 5. Performance and resiliency
- **Load testing** (Locust, k6): ramp concurrent users; measure p50/p95, TTFT, error rate; find the knee and the first saturated dependency (often model quotas or DB connections).
- **Throttling behaviour:** does the system degrade gracefully (queue, 429 + Retry-After) or collapse (timeouts, retry storms)?
- **Resiliency / chaos:** kill or slow a dependency, expire a token, return malformed data; verify timeouts, fallbacks, clear user messaging.

## 6. Security testing
- Prompt injection (direct + indirect via documents/tickets/emails), jailbreaks.
- Data exfiltration through tools (e.g. agent asked to email/post data, markdown image URLs).
- Over-permissioned tools: can the agent do more than the use case requires?
- Cross-tenant/user leakage in RAG and memory.
Turn every successful attack into a regression case (M12).

---

## Self-check (try first, then open)
<details><summary>How do you know a prompt change made the agent better rather than just different?</summary>

Run the versioned eval suite (golden set + scenarios) on old and new prompts with the same model/settings, multiple runs per case. Compare task success, tool accuracy, safety and cost with statistical care (variance, per-category breakdown), inspect cases that flipped in each direction, and check no critical case regressed. If possible, follow with a canary/A-B in production on real quality signals. "Better" is defined by the metrics you agreed with the customer.
</details>

<details><summary>What are the limits of LLM-as-judge?</summary>

Biases (verbosity, position, self-preference, leniency), inconsistency across runs and judge versions, inability to verify facts it doesn't know, susceptibility to injection in the graded output, cost/latency at scale, and rubric ambiguity. Mitigate with clear anchored rubrics, reference answers, deterministic checks first, calibration against human labels, a different model family as judge, and periodic human review.
</details>

## Resources
- AgentCore Evaluations and Bedrock model evaluation docs
- Anthropic docs: "Define success criteria" and "Develop tests"
- Papers/blogs on LLM-as-judge bias (e.g. "Judging LLM-as-a-Judge", Zheng et al.)
- Locust / k6 documentation
- OWASP Top 10 for LLM Applications (security test ideas)

**Next:** [Lab environment setup](../labs/SETUP.md) → [Lab 01](../labs/lab-01-scenario-eval-ci/README.md)
