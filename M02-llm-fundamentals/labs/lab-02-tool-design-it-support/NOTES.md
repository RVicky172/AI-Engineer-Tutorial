# Lab 02 Notes — Tool design for an IT-support agent

## What I built
Five service-desk tools (`get_ticket`, `search_kb`, `restart_service`, `add_comment`, `escalate`) defined twice, and two experiments that measure the difference:

1. **Selection** (`select`): 25 labelled requests, sent once per toolset. Scores which tools the model picks and whether the arguments pass the tool's contract. Nothing is executed.
2. **Recovery** (`recover`): a small agent loop against a fake service desk where some calls fail on purpose (frozen service, malformed number, missing incident, closed ticket, KB timeout). Compares **terse** errors (`Error 409`) with **actionable** ones that say what to do next.

```
data/build_dataset.py  requests.jsonl (25), parallel.jsonl (3, stretch), recovery.jsonl (6); every label has a `why`
src/tool_design/
├── args.py       Pydantic argument models: the contract (v2 schemas, backend validation, scoring)
├── toolsets.py   V1 (one-liners, free-text strings) and v2_tools() (generated from args.py, strict)
├── backend.py    FakeServiceDesk: tickets, KB, frozen services; terse vs actionable errors
├── selection.py  build_request, score_reply, run_all, summarise
├── agent.py      run_scenario(): the tool loop, is_error results, step limit, loop detection
├── report.py     results.md (v1 vs v2) and recovery.md (terse vs actionable, with transcripts)
└── cli.py        python -m tool_design select | recover
tests/            58 tests, 100% coverage, no network
```

### v1 vs v2: what changed
| | v1 | v2 |
|---|---|---|
| Description | "Restart a service." | what it does, **when to use**, **when NOT to use (and which tool instead)**, what it returns |
| Arguments | `{"type": "string"}` everywhere | enums (`service`, `group`, `visibility`), format + example in the description (`INC0012345`) |
| `strict` | off | on: shape and enums guaranteed |
| Property names | same as v2 | same as v1, so only the *description* differs |

## Commands to run it
```bash
cd M02-llm-fundamentals/labs && source .venv/bin/activate
cd lab-02-tool-design-it-support
pytest && ruff check . && mypy src tests                         # offline, free

python -m tool_design select --limit 5                           # live smoke test: 10 calls
python -m tool_design select                                     # 50 calls -> results.md
python -m tool_design recover                                    # ~30 calls -> recovery.md
python -m tool_design select --versions v2 --data data/parallel.jsonl --out results-parallel.md   # stretch
```

## Results / numbers
**Live run pending** (no model credentials were configured when this was built). Fill in from `results.md` / `recovery.md`:

| | v1 | v2 |
|---|---|---|
| Tool selection accuracy (25) | | |
| Ambiguous cases right (7) | | |
| Called a tool when none was needed | | |
| Argument validity | | |

| | terse errors | actionable errors |
|---|---|---|
| Recovered (6 scenarios) | | |
| Looping | | |

Predictions to test (write yours down *before* the run): v1 loses most on the ambiguous set (a01 "restart my spooler" → `restart_service`, a02 "let network know" → `escalate`) and on enum values (`networking`, `SSO login page`); v1 may invent an incident number for n04 "Restart the VPN gateway."; terse errors cause a retry of the same failing call (r01) and a guessed number (r02).

## What broke and how I fixed it
- **From the API reference, before writing code: `tool_choice: {"type": "any"}` returns a 400 on Claude Opus 5.5 / Sonnet 5.5.** It also would have made the no-tool cases meaningless. Selection runs on `auto`, which is also the honest measurement: real agents run on `auto`.
- **Found by printing the generated schema: `strict: true` doesn't enforce `pattern`.** `transform_schema` moves it into the description. So `INC12346` can still arrive; the backend validates every call with the same Pydantic model and returns an actionable error. Strict and validation are complementary.
- **Pitfall guarded: shared mutable history.** The fake records request kwargs by reference. Passing the growing `messages` list would make every recorded call show the *final* history, so the loop sends `list(messages)` per call and a test checks the length per step.
- **Design rule: keep the comparison fair.** If v1 used different property names (`id`, `q`), every v1 call would fail validation for a reason unrelated to descriptions. v1 differs from v2 only in descriptions, enums and strict, and a test enforces it (`test_v1_and_v2_differ_only_in_how_tools_are_described`).
- **A wrong test expectation.** I expected the fake's v1 run to produce 2 invalid calls (a01 and c11), but the fake's a01 `restart_service` call carried valid arguments: only c11 was invalid. The scorer was right and the test was wrong, a reminder to check which side is broken before "fixing" code.
- **Lenient labels inflate accuracy.** `also_ok` exists for genuinely ambiguous cases, but it's used once (a05). Each use is a judgement you should be able to defend.

## What I'd explain in an interview
1. **Descriptions do the selection work.** The model only sees name, description and schema. "When NOT to use, use X instead" fixes overlap between tools better than anything else.
2. **Enums beat free text.** `group: "networking"` is a valid string and an invalid group. An enum makes the wrong value impossible under strict mode.
3. **Errors are results.** Return `is_error: true` with what went wrong *and what to do next* ("Do not retry. Escalate to erp-support instead."). A bare `Error 409` invites blind retries.
4. **Measure before and after.** A labelled set with ambiguous and no-tool cases is the only way to know a description change helped and didn't break something else.
5. **Agent loops need stops.** A step limit, detection of repeated identical failing calls, and all parallel results in one message.

## Improve it yourself
1. Add a sixth tool that overlaps (`search_tickets`) and measure how much v2 accuracy drops: overlap is the main failure mode.
2. Run `select` 3 times and report the spread: is a 1-case difference between v1 and v2 real or noise?
3. Add `input_examples`-style examples to the v2 descriptions for `restart_service` and see whether argument correctness changes.
4. Put Lab 02's `ResilientClient` (M01) under a real HTTP backend and map its errors to the actionable messages here.
