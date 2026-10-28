import json
from pathlib import Path

import anthropic
import httpx2
import pytest
from llm_common import Settings
from llm_common.fake import FakeMessages, make_message, tool_use_block

from tests.conftest import MODEL, VALID_ARGS, answer_key
from tool_design.cli import main
from tool_design.dataset import Case
from tool_design.report import render_selection
from tool_design.selection import Outcome, run_all, run_case, score_reply, summarise
from tool_design.toolsets import Version

REQUEST = httpx2.Request("POST", "https://api.example.test/v1/messages")


def by_id(cases: list[Case], id_: str) -> Case:
    return next(c for c in cases if c.id == id_)


def test_right_tool_with_right_values_scores_fully(cases: list[Case]) -> None:
    c01 = by_id(cases, "c01")
    reply = make_message("Checking.", tool_use_block("get_ticket", {"number": "INC0012345"}))

    result = score_reply(c01, Version.V2, reply)

    assert result.selection_correct
    assert result.args_valid is True
    assert result.args_correct is True
    assert result.text == "Checking."


def test_valid_but_wrong_values_are_not_args_correct(cases: list[Case]) -> None:
    c01 = by_id(cases, "c01")
    reply = make_message(tool_use_block("get_ticket", {"number": "INC0012346"}))
    result = score_reply(c01, Version.V2, reply)
    assert result.selection_correct
    assert result.args_valid is True
    assert result.args_correct is False


def test_wrong_tool_and_invalid_args(cases: list[Case]) -> None:
    a01 = by_id(cases, "a01")
    reply = make_message(tool_use_block("restart_service", {"service": "print spooler"}))

    result = score_reply(a01, Version.V1, reply)

    assert not result.selection_correct
    assert result.args_valid is False
    assert result.args_correct is None  # not judged when the tool is wrong
    assert "service" in result.calls[0].error
    assert "ticket_number" in result.calls[0].error


def test_unknown_tool_name_is_an_invalid_call(cases: list[Case]) -> None:
    reply = make_message(tool_use_block("search_tickets", {"q": "laptop"}))
    result = score_reply(by_id(cases, "n03"), Version.V1, reply)
    assert result.calls[0].error == "unknown tool"


def test_answering_without_tools_is_right_for_no_tool_cases(cases: list[Case]) -> None:
    result = score_reply(by_id(cases, "n04"), Version.V2, make_message("Which incident?"))
    assert result.selection_correct
    assert result.args_valid is None
    assert result.args_correct is None


def test_also_ok_alternatives_count_and_order_does_not_matter(cases: list[Case]) -> None:
    a05 = by_id(cases, "a05")
    both = make_message(
        tool_use_block("search_kb", VALID_ARGS["search_kb"]),
        tool_use_block("get_ticket", {"number": "INC0012350"}),
    )
    assert score_reply(a05, Version.V2, both).selection_correct
    kb_only = make_message(tool_use_block("search_kb", VALID_ARGS["search_kb"]))
    assert not score_reply(a05, Version.V2, kb_only).selection_correct


@pytest.mark.parametrize(
    ("reply", "outcome"),
    [
        (make_message(stop_reason="refusal"), Outcome.REFUSAL),
        (make_message("partial", stop_reason="max_tokens"), Outcome.TRUNCATED),
    ],
)
def test_refusal_and_truncation_are_failures(
    cases: list[Case], reply: anthropic.types.Message, outcome: Outcome
) -> None:
    result = score_reply(by_id(cases, "n01"), Version.V2, reply)
    assert result.outcome is outcome
    assert not result.selection_correct


def test_run_case_records_usage_latency_and_api_errors(cases: list[Case]) -> None:
    ticks = iter([1.0, 1.5])
    fake = FakeMessages([make_message("hi", input_tokens=1000, output_tokens=100)])
    ok = run_case(fake, by_id(cases, "n02"), Version.V2, model=MODEL, clock=lambda: next(ticks))
    assert ok.latency_s == 0.5
    assert ok.tally.cost_usd == pytest.approx((1000 * 0.10 + 100 * 0.50) / 1_000_000)

    failing = FakeMessages([anthropic.APIConnectionError(request=REQUEST)])
    err = run_case(failing, by_id(cases, "n02"), Version.V2, model=MODEL)
    assert err.outcome is Outcome.API_ERROR
    assert err.tally.calls == 0


def test_configuration_errors_stop_the_run(cases: list[Case]) -> None:
    response = httpx2.Response(404, request=REQUEST)
    fake = FakeMessages([anthropic.NotFoundError("no such model", response=response, body=None)])
    with pytest.raises(anthropic.NotFoundError):
        run_case(fake, cases[0], Version.V1, model=MODEL)


def test_summary_compares_versions(cases: list[Case]) -> None:
    results = run_all(answer_key(cases), cases, list(Version), model=MODEL, workers=3)
    v1, v2 = summarise(results)

    assert v2.accuracy == 1.0
    assert v1.accuracy == 24 / 25  # a01 picked restart_service
    assert v1.by_category["ambiguous"] == (6, 7)
    assert v1.invalid_calls == 1  # c11: 'networking' is not a group (a01's args were valid)
    assert v2.invalid_calls == 0
    assert v2.arg_validity == 1.0
    assert v2.unneeded_calls == v2.missed_calls == v2.failures == 0
    assert v1.args_correct is not None and v1.args_correct < 1.0
    assert v2.cost_per_1k == pytest.approx((1200 * 0.10 + 80 * 0.50) / 1_000_000 * 1000)


def test_report_shows_both_versions_side_by_side(cases: list[Case]) -> None:
    results = run_all(answer_key(cases), cases, list(Version), model=MODEL)
    report = render_selection(summarise(results), results, header="h")

    assert "| Metric | v1 | v2 |" in report
    assert "| Tool selection accuracy | 96% | 100% |" in report
    assert "| a01 | ambiguous |" in report
    assert "| restart_service | ok |" in report
    assert "| c11 | v1 | escalate |" in report  # invalid enum value listed


def test_report_says_none_when_everything_is_right(cases: list[Case]) -> None:
    results = run_all(answer_key(cases), cases[:3], [Version.V2], model=MODEL)
    report = render_selection(summarise(results), results, header="h")
    assert "## Wrong tool choices\n\nNone." in report
    assert "## Invalid arguments\n\nNone." in report


def test_cli_select_writes_report_and_rows(
    cases: list[Case], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "results.md"
    code = main(
        ["select", "--limit", "4", "--out", str(out)],
        api=answer_key(cases),
        settings=Settings(model=MODEL),
    )
    assert code == 0
    assert "| Metric | v1 | v2 |" in out.read_text()
    rows = [json.loads(x) for x in out.with_suffix(".jsonl").read_text().splitlines()]
    assert len(rows) == 8
    assert "Total spend this run" in capsys.readouterr().out


def test_cli_select_parallel_stretch(parallel: list[Case], tmp_path: Path) -> None:
    out = tmp_path / "parallel.md"
    data = Path(__file__).resolve().parents[1] / "data" / "parallel.jsonl"
    main(
        ["select", "--versions", "v2", "--data", str(data), "--out", str(out)],
        api=answer_key(parallel),
        settings=Settings(model=MODEL),
    )
    assert "| Tool selection accuracy | 100% |" in out.read_text()
