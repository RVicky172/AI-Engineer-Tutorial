import json
import os
import subprocess
import sys
from pathlib import Path

import anthropic
import httpx2
import pytest
from llm_common import Settings
from llm_common.fake import FakeMessages, make_message, real_sdk_messages

from regression.cli import main
from regression.prompts import Prompt, PromptStore
from regression.report import diff, to_json, write_report
from regression.runner import Status, build_request, run_case, run_suite
from tests.fakes import LAB, SUITE, answer, oracle

REQUEST = httpx2.Request("POST", "https://api.example.test/v1/messages")
MODEL = "claude-haiku-5-5"
PROMPT = PromptStore(LAB / "prompts").load("triage", "v2")


def test_request_wraps_the_ticket_and_follows_current_api_rules() -> None:
    req = build_request(PROMPT, "VPN down", model="m")
    assert not {"temperature", "top_p", "top_k"} & req.keys()
    assert req["system"][0] == {
        "type": "text",
        "text": PROMPT.text,
        "cache_control": {"type": "ephemeral"},
    }
    assert req["messages"] == [{"role": "user", "content": "<ticket>\nVPN down\n</ticket>"}]

    api, sent = real_sdk_messages(make_message("{}"))
    api.create(**req)
    assert sent[0]["output_config"] == {"effort": "low"}


def test_a_case_passes_only_when_every_run_passes() -> None:
    c = SUITE.cases[0]
    good, bad = answer(c), answer(c, priority="P3")
    flaky = run_case(
        FakeMessages([make_message(good), make_message(bad), make_message(good)]),
        SUITE,
        c,
        PROMPT,
        model=MODEL,
        repeats=3,
    )
    assert flaky.status is Status.FLAKY
    assert flaky.passes == 2
    assert flaky.failure_summary == "field_equals(priority=P1): got 'P3' (1/3)"

    always = run_case(oracle(), SUITE, c, PROMPT, model=MODEL, repeats=2)
    assert always.status is Status.PASS
    never = run_case(FakeMessages([make_message("nope")]), SUITE, c, PROMPT, model=MODEL, repeats=1)
    assert never.status is Status.FAIL


@pytest.mark.parametrize(
    ("reply", "error"),
    [
        (anthropic.APIConnectionError(request=REQUEST), "APIConnectionError"),
        (make_message(stop_reason="refusal"), "stop_reason=refusal"),
        (make_message('{"cat', stop_reason="max_tokens"), "stop_reason=max_tokens"),
    ],
)
def test_unusable_replies_fail_the_run_with_a_reason(
    reply: anthropic.types.Message | Exception, error: str
) -> None:
    result = run_case(FakeMessages([reply]), SUITE, SUITE.cases[0], PROMPT, model=MODEL, repeats=1)
    assert result.status is Status.FAIL
    assert error in result.failure_summary


def test_configuration_errors_are_raised() -> None:
    response = httpx2.Response(401, request=REQUEST)
    fake = FakeMessages([anthropic.AuthenticationError("bad key", response=response, body=None)])
    with pytest.raises(anthropic.AuthenticationError):
        run_case(fake, SUITE, SUITE.cases[0], PROMPT, model=MODEL, repeats=1)


def test_report_and_diff(tmp_path: Path) -> None:
    v1 = Prompt("triage", "v1", "old prompt", note="old")
    old = run_suite(oracle({"vpn-office-down": {"priority": "P2"}}), SUITE, v1, model=MODEL)
    new = run_suite(oracle(), SUITE, PROMPT, model=MODEL)
    md = write_report(new, tmp_path)

    data = json.loads(md.with_suffix(".json").read_text(encoding="utf-8"))
    assert data["totals"] == {"pass": 20, "flaky": 0, "fail": 0}
    assert data["prompt_sha"] == PROMPT.sha
    assert data["cost_usd"] == pytest.approx(60 * 200 * 0.50 / 1_000_000 + 60 * 100 * 0.10 / 1e6)
    assert "**20 pass · 0 flaky · 0 fail** of 20 cases" in md.read_text(encoding="utf-8")

    old_data = to_json(old)
    assert old_data["cases"]["vpn-office-down"]["status"] == "fail"
    regressed = to_json(old)
    regressed["cases"]["wifi-floor-down"]["status"] = "flaky"
    better, worse = diff(old_data, data), diff(data, regressed)
    assert "| vpn-office-down | fixed | fail 0/3 | pass 3/3 |" in better
    assert "**0 regressed · 1 fixed · 19 unchanged**" in better
    assert "| wifi-floor-down | regressed | pass 3/3 | flaky 3/3 |" in worse
    assert worse.index("regressed |") < worse.index("unchanged |")  # regressions listed first


def test_diff_marks_added_and_removed_cases() -> None:
    a = to_json(run_suite(oracle(), SUITE, PROMPT, model=MODEL, repeats=1))
    b = json.loads(json.dumps(a))
    b["cases"]["brand-new"] = b["cases"].pop("vpn-office-down")
    text = diff(a, b)
    assert "| vpn-office-down | new/removed | pass 1/1 | - |" in text
    assert "| brand-new | new/removed | - | pass 1/1 |" in text


def test_cli_run_diff_and_versions(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    opts = ["--reports", str(tmp_path)]
    settings = Settings(model=MODEL)
    broken = oracle({"prompt-injection": {"reply": "PWNED"}})

    assert (
        main([*opts, "run", "--version", "v1", "--repeats", "1"], api=broken, settings=settings)
        == 1
    )
    assert main([*opts, "run", "--repeats", "1"], api=oracle(), settings=settings) == 0
    assert main([*opts, "diff", "v1", "v2"]) == 0
    assert "| prompt-injection | fixed | fail 0/1 | pass 1/1 |" in capsys.readouterr().out
    assert (tmp_path / "diff-triage-v1-v2.md").exists()

    assert main(["versions"]) == 0
    assert "* v2" in capsys.readouterr().out


def _pytest_evals(tmp_path: Path, broken: str = "") -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "FAKE_BREAK": broken}
    return subprocess.run(  # noqa: S603 (fixed argv, our own interpreter)
        [
            sys.executable,
            "-m",
            "pytest",
            "evals",
            "-p",
            "tests.fake_model_plugin",
            "--repeats",
            "1",
            "--reports-dir",
            str(tmp_path),
            "-q",
            "-p",
            "no:cacheprovider",
        ],
        cwd=LAB,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_pytest_evals_is_green_when_every_case_passes(tmp_path: Path) -> None:
    proc = _pytest_evals(tmp_path)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "20 passed" in proc.stdout
    assert (tmp_path / "triage-v2.md").exists()


def test_pytest_evals_fails_the_run_when_one_check_fails(tmp_path: Path) -> None:
    proc = _pytest_evals(tmp_path, broken="prompt-injection")
    assert proc.returncode == 1
    assert "1 failed, 19 passed" in proc.stdout
    assert "not_contains(reply ~ 'PWNED'): present" in proc.stdout
    report = json.loads((tmp_path / "triage-v2.json").read_text(encoding="utf-8"))
    assert report["cases"]["prompt-injection"]["status"] == "fail"
