# Lab 03 Notes — Prompt regression suite

## What I built
A regression gate for a ticket-triage prompt. The model returns `{"category", "priority", "reply"}`. A prompt change is a release: new version file → run the suite → diff the reports → move `CURRENT`.

```
prompts/triage/v1.md, v2.md   versioned prompts; front matter `note:` says what changed
prompts/triage/CURRENT        the version in use (v2)
evals/cases.yaml              20 cases: defaults (json_valid, max_tokens) + per-case checks
evals/conftest.py             --prompt-version, --repeats, --effort, --reports-dir; writes the report
evals/test_triage.py          one pytest test per case; a case passes only if ALL runs pass
src/regression/
├── prompts.py   PromptStore: versions (v2 < v10), CURRENT, front matter, sha of the text
├── checks.py    json_valid, field_equals, field_in, contains, not_contains, max_tokens
├── cases.py     Suite/Case models: unknown check types and duplicate ids fail at load
├── runner.py    run_case(): N runs in parallel → PASS / FLAKY / FAIL
├── report.py    reports/<task>-<version>.json + .md, and diff() between two versions
└── cli.py       python -m regression run | diff | versions
ci/prompt-regression.yml      stretch: GitHub Actions on prompts/** changes (copy to .github/ to enable)
tests/                        39 tests, 100% coverage, no network
```

v1 → v2 (the deliberate change): v1 lists the fields only. v2 adds category definitions, the priority rubric, reply rules (≤ 50 words, never ask for secrets, never promise a fix time, "disconnect" on compromise), untrusted-input handling, and an exact output format with "no code fences".

## Commands to run it
```bash
cd M02-llm-fundamentals/labs && source .venv/bin/activate
cd lab-03-prompt-regression-suite
pytest && ruff check . && mypy src tests evals           # offline unit tests, free

pytest evals/ --repeats 1 -k vpn                         # live smoke test: 2 calls
pytest evals/ --prompt-version v1                        # 60 calls -> reports/triage-v1.md
pytest evals/                                            # CURRENT (v2), 60 calls -> reports/triage-v2.md
python -m regression diff v1 v2                          # -> reports/diff-triage-v1-v2.md
python -m regression versions                            # list versions, * marks CURRENT
```
`pytest evals/` picks up `evals/pytest.ini`, so the live suite runs without the unit tests' coverage gate.

## Results / numbers
**Live run pending** (no model credentials were configured when this was built). Fill in from the reports:

| | v1 | v2 |
|---|---|---|
| pass / flaky / fail (20 cases, 3 runs) | | |
| cost | | |
| regressed / fixed (diff) | | |

Predictions to test: v1 fails `json_valid` where it wraps JSON in a fence, misses rubric-dependent priorities (`vpn-slow-workaround`, `phishing-reported-only`, `german-warehouse-wifi` with exactly 25 people), and has no reason to say "disconnect". Check whether any v2 case is **flaky**; each one is a finding to investigate, not noise to retry away.

## What broke and how I fixed it
- **The lab step "run with temperature 0" is no longer possible.** The current Claude API rejects `temperature`. That's fine: temperature 0 never made outputs identical anyway. Consistency is now *measured*: 3 runs per case, and FLAKY is its own status that fails the gate.
- **Real bug: a Python line continuation in a Markdown prompt.** I copied the rubric from Lab 01's Python string, `\` line endings included. In a `.md` file those reach the model as literal backslashes. A test now rejects `\` + newline in every prompt version.
- **Pitfall guarded: the live suite would inherit the unit tests' coverage gate.** The lab's `pyproject.toml` adds `--cov-fail-under=90`, so `pytest evals/` would fail on coverage even with every case green. `evals/pytest.ini` gives the live suite its own config, and the subprocess tests below prove it.
- **Proving the gate actually fails.** A gate that can't fail is decoration. Two tests run `pytest evals/` in a subprocess against a fake model: all green → exit 0; one case returns `PWNED` → exit 1, "1 failed, 19 passed", and the report marks that case `fail`.
- **`max_tokens` counts thinking.** The check reads billed `usage.output_tokens`, so it's a cost guard, not a length check. At higher effort the same reply costs more tokens.
- **Real bug: Windows file encoding.** `read_text()` without `encoding=` decodes as cp1252 on Windows and garbled the `·` in reports. Every read and write passes `encoding="utf-8"`.

## What I'd explain in an interview
1. **A prompt is code.** Versioned files, a test suite, a diff, a release pointer, and CI on change. "I tweaked the prompt in prod" is how regressions ship.
2. **Deterministic checks first.** JSON validity, exact fields, forbidden phrases and token budgets are cheap, exact and explainable. Add an LLM judge (M11) only for what these can't express.
3. **Flaky is a result.** The same input passing 2 of 3 times means the prompt is ambiguous for that case. Fix the prompt or the label; don't retry until green.
4. **Labels are the contract.** If a label can't be justified from the rubric, fix the rubric or the label. `field_in` exists for genuinely two-answer cases, and a test caps it at 3 uses.
5. **Tie results to exact inputs.** Each report stores the prompt's sha, model and effort, so "v2 passed" can't silently mean a different v2.

## Improve it yourself
1. Add a v3 that cuts the rubric down to save tokens; diff it against v2 and decide whether the savings justify any regression.
2. Run the suite on `claude-haiku-5-5` and `claude-opus-5-5`: which cases need the bigger model?
3. Add a `max_words` check on `reply` (the rule says ≤ 50 words) and see how often each version breaks it.
4. Enable the CI workflow on a branch and open a PR that changes `v2.md`.
