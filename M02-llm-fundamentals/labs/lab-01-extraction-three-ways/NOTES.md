# Lab 01 Notes — One extraction task, three techniques

## What I built
A runner that extracts `service`, `severity`, `requester` and `summary` from 30 labelled IT-support emails with three techniques, and measures each one on the same inputs:

| Technique | What changes | How the output is constrained |
|---|---|---|
| `plain` | instructions + "respond with only a JSON object" | nothing: the model may wrap it in prose or a fence |
| `fewshot` | `plain` + 3 worked examples in `<example>` tags | nothing, but the examples show the exact shape |
| `structured` | `output_config.format` with the JSON schema from `Ticket` | constrained decoding: the shape is guaranteed |

```
data/build_dataset.py   the 30 eval emails + 3 few-shot examples (never in the eval set); writes the JSONL
src/extraction/
├── schema.py    Ticket: the single source of truth (structured-output schema AND validator)
├── prompts.py   one shared system prompt + rubric; build_request() per technique
├── parsing.py   parse_reply(): refusal / truncated / parse error / schema error / ok
├── runner.py    extract_one() (+ optional repair turn), run_all() in a thread pool, summarise()
├── report.py    results.md: metrics as rows, techniques as columns, every wrong value listed
└── cli.py       python -m extraction
tests/           39 tests, 100% coverage, no network (scripted fake + real SDK on a mock transport)
```

## Commands to run it
```bash
cd M02-llm-fundamentals/labs && source .venv/bin/activate
cd lab-01-extraction-three-ways
pytest && ruff check . && mypy src tests          # offline, free

python -m extraction --limit 3                    # live smoke test: 9 calls
python -m extraction                              # full run: 90 calls -> results.md + results.jsonl
python -m extraction --repair --out results-repair.md   # stretch: one repair turn
LLM_MODEL=claude-haiku-5-5 python -m extraction --out results-haiku.md
```

## Results / numbers
**Live run pending** (no model credentials were configured when this was built). Run the commands above, then fill this table from `results.md` and write the 3-sentence conclusion there.

| | plain | fewshot | structured |
|---|---|---|---|
| Valid output | | | |
| All three fields correct | | | |
| Needed cleanup (fences / prose) | | | |
| Cost per 1k emails | | | |

What to look for: does `structured` reach 30/30 valid while `plain` needs cleanup? Is `fewshot` more *accurate* (severity especially) or only better *formatted*? How much do the examples add to input tokens, and does caching win that back?

## What broke and how I fixed it
The failure modes this lab's code handles, each pinned by a test:

- **Old API habits fail loudly.** `temperature=0` and an assistant prefill (`{"role": "assistant", "content": "{"}`) both return 400 on current models. A test asserts no request sends either, so a copied snippet can't reintroduce them.
- **The schema the API accepts isn't the schema you wrote.** `transform_schema(Ticket)` adds `additionalProperties: false` and *moves* `pattern` and `maxLength` into descriptions. Structured output guarantees the shape, not every constraint, so every reply is still validated with Pydantic (`test_structured_request_sends_an_api_ready_schema`).
- **`content[0]` is not the answer.** Replies can start with a thinking block. `text_of()` joins only text blocks.
- **A truncated reply can still parse.** If `max_tokens` cuts off after a closing brace, `json.loads` succeeds on half an answer. `stop_reason` is checked *before* parsing.
- **Repairing the wrong failures wastes money.** Only parse and schema errors get a repair turn; refusals and truncations would just fail again at double the cost.
- **Failures are misses, not exclusions.** Excluding unparseable replies from accuracy makes a fragile technique look better than it is. Accuracy is over all 30 emails.

## What I'd explain in an interview
1. **Separate "couldn't parse" from "parsed but wrong".** They have different fixes: format problems go away with structured output; wrong values need a better rubric or examples.
2. **Read tokens from `usage`, never estimate.** Thinking tokens are billed as output tokens you never see; `input_tokens` excludes cached tokens.
3. **One source of truth for the schema.** The Pydantic model generates the API schema and validates the result, so they can't drift.
4. **Hold everything constant except the technique.** Same system prompt and rubric for all three, so the comparison measures the technique, not a better prompt.
5. **Repair loops have a cost/benefit you can measure.** `--repair` reports how many failures one extra call fixed, and what it cost.
