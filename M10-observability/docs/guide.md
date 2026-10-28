# M10 · Observability and Production Troubleshooting — Study Guide

> **Priority:** Must have · **Week:** 7 · **Study time:** ~3 h · **Labs:** [../labs](../labs/SETUP.md)

## Why it matters
Production troubleshooting is core to the role. The strongest candidates can explain **how they find root cause in minutes**: which signal they look at first, and how they isolate the failing layer.

## Learning objectives
- Use logs, metrics and traces together; write CloudWatch Logs Insights queries.
- Instrument an agent with OpenTelemetry, including model and tool spans.
- Define agent-specific signals and alarms.
- Follow a repeatable incident method and write post-incident notes.
- Find latency and cost hot spots.

---

## 1. Three pillars
| Pillar | Answers | AWS |
|---|---|---|
| **Logs** | what exactly happened in this request? | CloudWatch Logs, Logs Insights |
| **Metrics** | how much / how often / how fast, over time? | CloudWatch Metrics, EMF, alarms, dashboards |
| **Traces** | where did time go, which component failed, across services? | X-Ray / CloudWatch Application Signals, OpenTelemetry (ADOT) |
Glue them with IDs: every log line carries `trace_id`, `request_id`, `session_id`.

Logs Insights examples:
```sql
fields @timestamp, level, message, request_id
| filter level = "ERROR"
| stats count() by bin(5m)

fields @timestamp, model_id, latency_ms, input_tokens, output_tokens
| stats pct(latency_ms, 50) as p50, pct(latency_ms, 95) as p95,
        sum(input_tokens) as tin, sum(output_tokens) as tout by model_id, bin(1h)
```

## 2. OpenTelemetry
- **Span:** one timed operation (name, start/end, attributes, status, events). **Trace:** tree of spans for one request.
- **Context propagation:** trace ID passed in headers (W3C `traceparent`) so downstream services join the same trace.
- **Auto-instrumentation** for FastAPI, httpx, botocore; **manual spans** for agent steps.
- **GenAI semantic conventions:** attributes like `gen_ai.request.model`, `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`, `gen_ai.operation.name`.

```python
from opentelemetry import trace
tracer = trace.get_tracer("triage-agent")

async def call_tool(name: str, args: dict):
    with tracer.start_as_current_span(f"tool.{name}") as span:
        span.set_attribute("tool.name", name)
        span.set_attribute("tool.args_keys", ",".join(args))      # not raw values (PII)
        try:
            result = await TOOLS[name](**args)
            span.set_attribute("tool.success", True)
            return result
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR))
            raise
```
Export to Jaeger locally, to CloudWatch/X-Ray via ADOT in AWS, or to the customer's vendor (Datadog, Dynatrace) via OTLP.

**AgentCore Observability** gives session and trace views, tool-call spans, latency/error breakdowns in CloudWatch out of the box for agents on Runtime (and for others instrumented with ADOT).

## 3. Agent-specific signals
| Signal | Why |
|---|---|
| Tokens per request (in/out), cost per task | cost control, detect loops/context bloat |
| Time to first token, total latency p50/p95 | user experience |
| Steps (model calls) per task | loops, inefficient reasoning |
| Tool-call success rate, per tool | broken integrations |
| Guardrail interventions | attacks, false positives |
| Retrieval hit quality (top score, empty results) | RAG health |
| Task success / escalation rate / user feedback | quality (not visible in 5xx!) |
| Throttles | quota issues |

Alarms: error rate, p95 latency vs. SLO, tool failure rate, DLQ depth, token/cost anomaly. Alert on **symptoms users feel**, investigate with the rest.

## 4. Incident method
1. **Reproduce:** get one failing request/session/trace ID; note scope (all users? one tenant? one tool? since when?).
2. **Isolate the layer** (outside-in): client/API → identity/IAM → network → model → prompt/context → tools/integrations → RAG → infrastructure → cost. See [troubleshooting cheat sheet](../../interview-prep/troubleshooting-cheatsheet.md).
3. **Correlate with change:** deployments, prompt/model/config changes, upstream incidents, traffic patterns.
4. **Fix** one thing at a time; **verify** with the failing case + eval suite.
5. **Post-incident note:** timeline, impact, root cause, contributing factors, detection gap, actions.

## 5. Cost and latency analysis
- Rank prompts/tasks by total tokens → find bloated system prompts, giant tool results, missing caching.
- Trace waterfall → slow tools, sequential calls that could be parallel, retries.
- Compare steps-per-task distributions before/after releases.
- Check for retry storms (same error repeating within a trace).

---

## Self-check (try first, then open)
<details><summary>Users report the agent is slow only in the afternoon. How do you investigate?</summary>

Time-correlated → load or external dependency. Compare p50/p95 latency and request volume by hour; split latency by span (model call vs. tools vs. retrieval). Check Bedrock throttling/retries (quota hit at peak), TTFT increase, downstream API latency (customer systems busy in their business hours), connection pool exhaustion, autoscaling lag, scheduled jobs (batch, index syncs) competing for resources. Confirm with traces from slow vs. fast periods; fix (quota, cross-region profile, caching, scaling, rate limiting) and verify.
</details>

<details><summary>The agent answers confidently but incorrectly after a release. What do you compare?</summary>

Diff what changed in the release: prompt version, tool descriptions/schemas, model ID/version or inference parameters, guardrail config, retrieval config (chunking, index, filters, k), code. Compare eval results before/after on the golden set; pull traces of bad answers and compare retrieved context and tool outputs with a good run. Roll back the suspect component (prompt flag first), add the failing cases to the regression suite.
</details>

## Resources
- CloudWatch Logs Insights query syntax; Embedded Metric Format; CloudWatch alarms & metric math
- OpenTelemetry Python docs; OTel GenAI semantic conventions; AWS Distro for OpenTelemetry (ADOT)
- AgentCore Observability docs
- Google SRE book: Monitoring distributed systems; Postmortem culture

**Next:** [Lab environment setup](../labs/SETUP.md) → [Lab 01](../labs/lab-01-otel-tracing/README.md)
