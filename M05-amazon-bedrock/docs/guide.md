# M05 · Amazon Bedrock — Study Guide

> **Priority:** Must have · **Week:** 4 · **Study time:** ~3 h · **Labs:** [../labs](../labs/SETUP.md)

## Why it matters
Bedrock is the model layer for every solution in this role. You need to know the **APIs, quotas, security and production features** well enough to debug them at 2 a.m., not just click around the console.

## Learning objectives
- Call models with Converse / ConverseStream, including tool use, and know when InvokeModel is still used.
- Choose models and inference profiles; handle quotas and throttling.
- Configure Guardrails and understand where they apply.
- Use Knowledge Bases, prompt caching, batch inference and model evaluation appropriately.
- Control cost; lock down networking (VPC endpoints) and IAM; enable invocation logging.

---

## 1. APIs
| API | Use |
|---|---|
| **Converse** / **ConverseStream** | Unified, model-agnostic chat API: messages, system prompt, `inferenceConfig`, `toolConfig`, `guardrailConfig`. Default choice. |
| **InvokeModel** / **InvokeModelWithResponseStream** | Model-native request body. Needed for some models/features (e.g. embeddings) or provider-specific parameters. |
| **ApplyGuardrail** | Run a guardrail on any text (user input, tool output) without calling a model. |
| Batch inference | Large offline jobs from S3 at lower cost. |

```python
import boto3
from botocore.config import Config

brt = boto3.client("bedrock-runtime", config=Config(retries={"mode": "adaptive", "max_attempts": 6}))

resp = brt.converse(
    modelId=MODEL_ID,                     # often an inference profile ID, e.g. "us.<provider>.<model>"
    system=[{"text": "You are an IT triage assistant."}],
    messages=[{"role": "user", "content": [{"text": "payments-api 5xx spike"}]}],
    inferenceConfig={"maxTokens": 512, "temperature": 0.2},
    toolConfig={"tools": [{"toolSpec": {
        "name": "get_service_status",
        "description": "Current health of a service.",
        "inputSchema": {"json": {"type": "object",
                                 "properties": {"service": {"type": "string"}},
                                 "required": ["service"]}}}}]},
)
resp["stopReason"]   # "end_turn" | "tool_use" | "max_tokens" | "guardrail_intervened" | ...
resp["usage"]        # inputTokens, outputTokens, totalTokens
```
**Tool loop:** when `stopReason == "tool_use"`, find `toolUse` blocks in `resp["output"]["message"]["content"]`, run the tools, append the assistant message and a user message containing `toolResult` blocks (`toolUseId`, `content`, optional `status: "error"`), call again.

## 2. Model selection, inference profiles, quotas
- **Model access** must be enabled per account/region (some models need a use-case form).
- Select by task: small/fast model for classification and routing; larger model for complex reasoning and tool orchestration. Check context window, tool-use support, latency and price.
- **Inference profiles:** cross-region inference profiles route requests across several regions for higher throughput (IDs prefixed e.g. `us.`/`eu.`/`apac.`/`global.`). Some newer models are only invokable through a profile. Understand data-residency implications for customers.
- **Quotas:** requests per minute and tokens per minute per model per region (Service Quotas console). Exceeding them → `ThrottlingException` (HTTP 429).

**Handling throttling, in order:** retries with backoff + jitter (adaptive mode) → reduce tokens per request (caching, trimming) → smooth traffic (queue/semaphore) → cross-region inference profile → request a quota increase → provisioned throughput for steady high volume → route some traffic to another model.

## 3. Guardrails
A guardrail is a reusable policy you attach to Converse/InvokeModel calls (or call via ApplyGuardrail):
| Policy | Example |
|---|---|
| Content filters | hate, violence, sexual, misconduct, **prompt attack** — with strength levels |
| Denied topics | "investment advice", "competitor pricing" — defined in natural language + examples |
| Word filters | profanity, custom block-lists |
| Sensitive information (PII) | **block** or **anonymise/mask** emails, phones, card numbers; custom regex |
| Contextual grounding | checks answer is grounded in the provided source and relevant to the query |
Guardrails are versioned; the response `trace` shows which policy intervened. They are one layer — not a substitute for least-privilege tools and approvals (M12).

## 4. Other production features
- **Knowledge Bases:** managed RAG (M03).
- **Prompt management:** versioned prompt templates stored in Bedrock.
- **Prompt caching:** cache checkpoints on stable prefixes (system, tools, documents) → lower cost and latency on repeated calls. Check model support.
- **Batch inference:** lower price for non-real-time jobs (nightly classification, eval runs).
- **Model evaluation:** automatic and human evaluation jobs to compare models on your data.

## 5. Cost control
- Log tokens per request (from `usage`) with model ID and feature tags; compute cost per task.
- Cache stable prefixes; trim context; cap `maxTokens`.
- **Route**: small model first, escalate to a large model only when needed (by classifier or confidence).
- Avoid retry storms and agent loops (cost spikes usually come from these).
- Set AWS Budgets and anomaly detection.

## 6. Security and networking
- **IAM:** `bedrock:InvokeModel` / `bedrock:InvokeModelWithResponseStream` (Converse uses the same actions) scoped to specific foundation-model and inference-profile ARNs. Cross-region profiles need permission on the profile and on the underlying models in each target region.
- **VPC endpoint (PrivateLink):** interface endpoint `com.amazonaws.<region>.bedrock-runtime` with private DNS lets workloads in private subnets call Bedrock without internet/NAT. Endpoint policies can restrict principals/actions.
- **Model invocation logging:** request/response bodies + metadata to CloudWatch Logs and/or S3. Great for debugging and cost analysis; contains sensitive data → restrict access, encrypt with KMS, set retention.
- Data handling: understand and be able to explain the provider's terms for prompts/completions (not used to train base models, stays in region unless you use cross-region inference) — verify current AWS wording.

---

## Self-check (try first, then open)
<details><summary>You see intermittent ThrottlingException in production. What are your options, in order?</summary>

1) Confirm: which model/region, RPM vs TPM limit, correlation with traffic peaks (CloudWatch metrics, invocation logs). 2) Retries with exponential backoff + jitter (adaptive retry mode), at one layer only. 3) Reduce tokens per request (caching, trimming, smaller max tokens). 4) Smooth bursts with a queue/semaphore and backpressure. 5) Use a cross-region inference profile. 6) Request a quota increase. 7) Provisioned throughput for steady high load. 8) Route a share of traffic to another model as fallback.
</details>

<details><summary>How would you route simple vs. complex requests to different models and measure the savings?</summary>

Add a cheap classifier (rules or small model) that labels requests simple/complex; simple → small model, complex → large model; optionally escalate if the small model's output fails validation or confidence is low. Measure with your eval set: quality per route vs. all-large baseline, and cost per task from token logs (tokens × price per model). Roll out behind a feature flag, compare A/B, and track escalation rate.
</details>

## Resources
- Amazon Bedrock User Guide: Converse API, Tool use, Inference profiles, Quotas, Guardrails, Prompt caching, Model invocation logging, VPC interface endpoints
- AWS Service Quotas console (Bedrock)
- AWS "What's New" feed for Bedrock

**Next:** [Lab environment setup](../labs/SETUP.md) → [Lab 01](../labs/lab-01-converse-client/README.md)
