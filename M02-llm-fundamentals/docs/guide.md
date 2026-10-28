# M02 · LLM Fundamentals, Prompting, Tool Calling and Structured Outputs — Study Guide

> **Priority:** Must have · **Week:** 1 · **Study time:** ~3 h · **Labs:** [../labs](../labs/SETUP.md)

## Why it matters
Every agent problem eventually traces to one of three things: **the model, the prompt, or the tool contract**. You need to reason about all three quickly when a customer says "the agent is doing something weird".

## Learning objectives
- Explain tokens, context windows, sampling parameters, latency and cost in practical terms.
- Write prompts with clear structure, constraints and examples, and version them like code.
- Design tool schemas that the model selects and fills correctly.
- Get reliable structured output and recover from schema failures.
- Manage context and cost on long sessions; recognise the main failure modes.

---

## 1. How LLMs work (practical level)
| Concept | What you need to know |
|---|---|
| **Tokens** | Models read/write tokens (~3-4 characters of English each). Pricing, limits and latency are all per token. |
| **Context window** | Max tokens for input + output in one call. Everything the model "knows" about the conversation must fit. |
| **Output tokens** | Generated one at a time → output length dominates latency. Output is usually priced several times higher than input. |
| **Temperature / top-p** | Randomness of sampling. Use low values for extraction/classification and tools; higher for creative text. Low temperature reduces but does not eliminate variation. |
| **Stop sequences / max tokens** | Hard limits; a `max_tokens` stop reason means truncated output (a common cause of broken JSON). |
| **Latency** | ≈ time-to-first-token (input processing, queueing) + output tokens × per-token time. Stream to improve perceived latency. |

**Cost formula:** `cost = input_tokens × input_price + output_tokens × output_price` (cached input tokens are cheaper). Always read token counts from the API's `usage` field rather than estimating.

## 2. Prompt engineering patterns
A good system prompt is a **spec**, not a vibe:
```text
You are an IT incident triage assistant for ACME's operations team.

<goal>Classify the incident and propose the next diagnostic step.</goal>

<rules>
- Only use information from the incident and tool results. If unsure, say so.
- Never perform restarts or closures without calling request_approval first.
- Answer in under 120 words.
</rules>

<output_format>JSON matching the provided schema.</output_format>
```
Patterns:
- **Role + goal + constraints + output format**, in that order.
- **Delimiters** (XML tags) separate instructions from data — and mark untrusted content (`<retrieved_document>`), which also helps against injection.
- **Few-shot examples** for format and edge cases; keep them diverse and representative.
- **Reasoning:** asking the model to think step by step (or enabling extended thinking where supported) helps on complex tasks but costs tokens and latency; prefer concise reasoning for simple classification.
- **Prompt versioning:** prompts live in files under git, have versions, and are tested by a regression suite (Lab 03). A prompt change is a release.

## 3. Tool / function calling
The model never executes anything. It returns a **structured request** ("call `get_ticket` with `{id: INC0012345}`"); your code runs it and sends back the result.

```
user msg → model → tool_use(name, input) → your code runs tool → tool_result → model → … → final answer
```

Good tool design:
- **Name and description do the selection work.** Say what it does, when to use it, when *not* to, and what it returns.
- **Tight schemas:** enums instead of free text, patterns (`^INC\d{7}$`), required fields, examples in descriptions.
- **Few, distinct tools** beat many overlapping ones. Overlap → wrong tool choice.
- **Errors are results:** return a short, actionable error ("ticket not found; numbers look like INC0012345") and flag it as an error so the model can recover.
- **Parallel tool calls:** models may request several independent tools in one turn; run them concurrently and return all results.
- **Compact results:** return only the fields the model needs. Huge tool results burn context and confuse the model.

```python
get_ticket = {
  "name": "get_ticket",
  "description": "Fetch one incident by number. Use when the user mentions an INC number. "
                 "Does NOT search; use search_tickets for free-text queries.",
  "input_schema": {
    "type": "object",
    "properties": {"number": {"type": "string", "pattern": "^INC\\d{7}$"}},
    "required": ["number"]
  }
}
```

## 4. Structured outputs
Options from weakest to strongest:
1. "Respond in JSON" in the prompt → parse → validate with Pydantic.
2. Prefill / format instructions + examples.
3. **Tool-use as extraction:** define a tool whose input schema is your output schema and force the model to call it.
4. **Native structured outputs / JSON-schema enforcement** where the provider supports it (check your model/API).

Always: validate with Pydantic, and on failure run a **repair loop** — send the validation error back once, re-ask, then fail cleanly. Watch for `max_tokens` truncation.

## 5. Context management and cost
- **Prompt caching:** stable prefix (system prompt, tool definitions, long documents) is cached; repeated calls pay a reduced rate and get lower latency. Put stable content first, variable content last.
- **Trim tool results** and keep only relevant history.
- **Summarise** older turns into a running summary; keep the last N turns verbatim.
- **Model routing:** small, cheap model for classification/routing; large model only for hard reasoning.
- **Cap output** with `max_tokens` and concise-answer instructions.

## 6. Failure modes
| Failure | Typical cause | Mitigation |
|---|---|---|
| Hallucination | missing info, pressure to answer | grounding (RAG), "say I don't know", citations, groundedness checks |
| Prompt injection | instructions inside user/tool/retrieved content | delimit untrusted data, least-privilege tools, approval, guardrails (M12) |
| Tool misuse | vague/overlapping descriptions | clearer descriptions, enums, fewer tools, examples |
| Looping | tool keeps failing, no stop condition | max steps, error results with hints, detect repeated identical calls |
| Refusal | over-cautious safety triggers | clarify legitimate context in system prompt; test with evals |
| Schema drift | prompt/model change breaks format | schema enforcement, validation, regression suite |

---

## Self-check (try first, then open)
<details><summary>Why would a model repeatedly call the wrong tool, and how do you fix it without changing the model?</summary>

Causes: overlapping or vague descriptions, misleading names, too many tools, no "when not to use" guidance, ambiguous user input, tool errors that don't explain what to do, or system prompt instructions that conflict. Fix: rewrite descriptions (purpose, when to use/not use, examples), merge/remove overlapping tools, use enums and strict schemas, return actionable errors, add a few-shot example, and measure tool-selection accuracy on a labelled set before/after (M02 Lab 02).
</details>

<details><summary>How do you reduce token spend on a long-running agent session by 40%?</summary>

Measure first (tokens per turn by component: system prompt, tools, history, tool results). Then: enable prompt caching for the stable prefix; trim/compact tool results; summarise old history; drop unused tool definitions or load tools on demand; route simple steps to a smaller model; cap output length; avoid retries/loops. Verify with your eval suite that quality didn't drop.
</details>

## Resources
- Anthropic docs: Prompt engineering overview, Tool use, Prompt caching, Structured outputs
- Amazon Bedrock User Guide: Converse API, tool use, prompt caching
- OWASP Top 10 for LLM Applications (failure modes)

**Next:** [Lab environment setup](../labs/SETUP.md) → [Lab 01](../labs/lab-01-extraction-three-ways/README.md)
