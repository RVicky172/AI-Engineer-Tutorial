# M02 Learnings — what the labs taught, and what to do better

The three labs are built and pass every offline gate (`labs/check.sh`: 150 tests across four projects, 100% coverage, ruff, mypy `--strict`). **Live runs against a real model are still to do**: each lab's `NOTES.md` has the commands, a results table to fill in, and predictions to check. Read each lab's `NOTES.md` for details.

| Lab | Offline result | Most important lesson |
|---|---|---|
| [01 Extraction, three ways](labs/lab-01-extraction-three-ways/NOTES.md) | 39 tests · 100% | Count "couldn't parse" separately from "parsed but wrong": they have different fixes |
| [02 Tool design](labs/lab-02-tool-design-it-support/NOTES.md) | 58 tests · 100% | Descriptions do the selection work; errors are results that must say what to do next |
| [03 Prompt regression suite](labs/lab-03-prompt-regression-suite/NOTES.md) | 39 tests · 100% | A prompt change is a release, and FLAKY is a result, not noise |
| [common/](labs/common/) `llm_common` | 14 tests · 100% | One provider switch, one cost formula and one fake model, shared by all labs |

---

## 1. Habits that showed their value (keep doing them)

1. **Check the current API before writing code.** Three things the study guide used to recommend now return a 400 on current Claude models: `temperature`/`top_p`, assistant prefill, and forced `tool_choice` (`any`/`tool`). Each lab has a test asserting its requests send none of them.
2. **Test with real SDK types and the real SDK.** `make_message()` builds genuine `Message` objects, and `real_sdk_messages()` runs the real client over an in-memory transport. Fakes alone can't tell you the SDK rejects a keyword or how it serialises a request.
3. **One source of truth for every contract.** Lab 01's `Ticket` and Lab 02's argument models generate the schema the API sees *and* validate what comes back. Lab 03's labels are checked against the categories the prompt actually lists.
4. **Prove the gate can fail.** Lab 03 runs `pytest evals/` in a subprocess against a fake that breaks one case, and asserts exit code 1. A gate that has never failed in a test is decoration.
5. **Hold everything constant except the variable.** Same rubric for all three Lab 01 techniques, same property names for both Lab 02 toolsets, same tools for both Lab 02 error styles.
6. **Label with a reason.** Every Lab 02 request carries a `why`, and Lab 03 caps lenient `field_in` labels at three. If you can't justify a label, the label or the rubric is wrong, not the model.

## 2. Mistakes made while building (learn from these)

| Mistake | Why it's tempting | Better approach |
|---|---|---|
| Copying a Python string, `\` continuations included, into a Markdown prompt | The rubric "already exists" | Prompts are data files: test them for artefacts (Lab 03 now does) |
| Reading files without `encoding="utf-8"` | Works on macOS and Linux | Windows defaults to cp1252. Always pass the encoding |
| Expecting 2 invalid calls from a fake that produced 1 | Writing the assertion from memory of the fixture | When a test fails, first check which side is wrong: code or test |
| Assuming `strict: true` enforces every schema keyword | "Strict" sounds absolute | It guarantees shape and enums; `pattern` and lengths move into descriptions. Validate in code too |
| Asserting on two diff reports concatenated into one string | Saves a line | One assertion target per behaviour |

## 3. Things that will surprise you on the live run

- **Caching may not kick in.** These system prompts and tool lists are short. Below the model's minimum cacheable prefix, `cache_control` silently does nothing: check `Cache read tokens` in the reports before claiming caching saved money.
- **You pay for thinking you don't see.** `output_tokens` includes thinking. Compare "Avg output tokens" against the length of the JSON you got back.
- **Effort is a real lever.** All labs default to `--effort low`. Re-run one lab at `medium` and compare accuracy against cost.
- **One run is one sample.** A 1-case difference out of 25 can be noise. Lab 03's repeats show how much the same input varies; apply that scepticism to Labs 01 and 02.

## 4. How these labs connect to the rest of the course

- `llm_common.make_messages_api` (Claude API or Bedrock, same Messages API) → **M05** adds Bedrock's own Converse API.
- Lab 02's tool contracts, `is_error` results and step limit → the agent loop in **M04**, and real ServiceNow tools behind MCP in **M07**.
- Lab 02's `FakeServiceDesk` → wrap M01's `ResilientClient` in tools and map its errors to actionable messages (M07).
- Lab 03's suite → grows into scenario evals and LLM judges in **M11**; the CI workflow runs in **M09**.
- Prompt-injection handling (`<request>`/`<ticket>` tags, the `prompt-injection` case) → **M12**.

## 5. Improvements to how you study this module

1. **Attempt each lab first.** 60-90 minutes from the lab README *without* opening `src/`, then diff against the reference and write 3 differences in `docs/notes.md`.
2. **Predict, then run.** Each `NOTES.md` lists predictions. Write your own before the live run, then score them. Wrong predictions are the most useful part.
3. **Run cheap first.** `--limit 3` / `--repeats 1` smoke tests cost cents. Full runs: Lab 01 is 90 calls, Lab 02 about 80, Lab 03 60 per prompt version.
4. **Break things on purpose.** Remove the `stop_reason` check in Lab 01's `parse_reply`, the `is_error` flag in Lab 02's `tool_result_block`, or the FLAKY status in Lab 03, and predict which test fails before running it.
5. **Answer the self-check questions aloud** (in `README.md`). Both are answered by these labs:
   - *Why would a model repeatedly call the wrong tool?* → Lab 02: vague or overlapping descriptions, no "when NOT to use", free-text arguments, and errors that don't say what to do next.
   - *Cut token spend 40% on a long session?* → measure first (Lab 01's per-technique token table), then caching (check it actually hits), effort, compact tool results (Lab 02's backend), and a smaller model where the regression suite (Lab 03) says quality holds.

## 6. Changes made to the lab setup
- `labs/common/` (`llm_common`): provider switch (Claude API / Bedrock Mantle), `UsageTally` and `cost_usd` from `usage`, `FakeMessages`, `real_sdk_messages`.
- `labs/requirements.txt` installs `common` and all three labs editable, plus pytest-cov, ruff, mypy and types-PyYAML.
- `labs/.env.example`: `LLM_PROVIDER` / `LLM_MODEL` replace the unused `BEDROCK_*_MODEL_ID` variables.
- `labs/check.sh`: every offline gate for every project; works with both `.venv/bin` and Windows `.venv/Scripts`.
- `docs/guide.md`: updated for the current API (no sampling parameters or prefill, effort and thinking tokens, strict tools, `is_error`, no forced `tool_choice`, `output_config.format`, minimum cacheable prefix).
