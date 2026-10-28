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
| **Temperature / top-p** | Randomness of sampling. On the current Claude API (version `2026-10-21`) sending `temperature`, `top_p` or `top_k` returns a **400**; other providers still accept them. Even temperature 0 never guaranteed identical outputs, so measure consistency instead: run each eval case several times (Lab 03). |
| **Thinking and effort** | Current Claude models reason before answering (adaptive thinking). `output_config.effort` (`low` … `max`) trades depth for tokens and latency; `low` suits extraction and classification. Thinking tokens are billed as **output** tokens even when you don't see them. |
| **Stop sequences / max tokens** | Hard limits; a `max_tokens` stop reason means truncated output (a common cause of broken JSON). Thinking counts toward `max_tokens`, so don't set it too low. |
| **Latency** | ≈ time-to-first-token (input processing, queueing) + output tokens × per-token time. Stream to improve perceived latency. |

**Cost formula:** `cost = input_tokens × input_price + cache_read × cache_read_price + cache_write × cache_write_price + output_tokens × output_price`. In Claude's `usage`, `input_tokens` excludes cached tokens and `output_tokens` includes thinking. Always read token counts from `usage` rather than estimating (`llm_common.pricing` does this for the labs).

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
- **Reasoning:** current Claude models think on their own (adaptive thinking); you steer *how much* with `effort`, not with "think step by step". More effort helps complex tasks but costs tokens and latency; use `low` for simple classification and extraction.
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
- **Strict mode:** `"strict": true` on a tool guarantees the arguments match the schema's shape and enums. It does *not* enforce `pattern` or `minLength`/`maxLength`: the SDK's `transform_schema` moves those into the description, so validate arguments in your code too (Lab 02).
- **Errors are results:** return a short, actionable error ("ticket not found; numbers look like INC0012345") as a `tool_result` with `"is_error": true`, so the model can recover instead of retrying blindly.
- **Parallel tool calls:** models may request several independent tools in one turn; run them concurrently and return **all** results in **one** user message (splitting them teaches the model to stop calling in parallel).
- **`tool_choice`:** leave it at `auto`. Forcing a call (`any` / `tool`) returns a 400 on Claude Opus 5.5 and Sonnet 5.5; steer with the description and prompt instead, and check whether a call was made.
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
2. Format instructions + few-shot examples. (Assistant *prefill* — starting the model's reply with `{` — returns a 400 on current Claude models.)
3. **Tool-use as extraction:** define a tool whose input schema is your output schema. Forcing the call needs `tool_choice: any/tool`, which current Opus/Sonnet reject, so prefer option 4.
4. **Native structured outputs:** `output_config: {"format": {"type": "json_schema", "schema": ...}}` (constrained decoding). Build the schema from your Pydantic model with `anthropic.transform_schema(Model)`.

Always: validate with Pydantic — even option 4 doesn't enforce every constraint — and on failure run a **repair loop**: send the validation error back once, re-ask, then fail cleanly. Check `stop_reason` first: `max_tokens` means truncated output and `refusal` means no answer; repairing either just pays twice (Lab 01).

## 5. Context management and cost
- **Prompt caching:** stable prefix (system prompt, tool definitions, long documents) is cached; repeated calls pay a reduced rate and get lower latency. The prefix renders as tools → system → messages: put stable content first, variable content last. A prefix below the model's minimum (hundreds to a few thousand tokens) silently doesn't cache: verify with `usage.cache_read_input_tokens`.
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
