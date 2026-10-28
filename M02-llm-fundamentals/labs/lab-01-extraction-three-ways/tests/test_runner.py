import json
from pathlib import Path

import anthropic
import httpx2
import pytest
from llm_common import Settings
from llm_common.fake import FakeMessages, make_message

from extraction.cli import main
from extraction.parsing import Outcome
from extraction.prompts import Technique
from extraction.report import render
from extraction.runner import extract_one, run_all, summarise
from extraction.schema import LabelledEmail
from tests.conftest import MODEL, answer_key, ticket_json

REQUEST = httpx2.Request("POST", "https://api.example.test/v1/messages")


def test_extract_one_records_tokens_cost_and_latency(emails: list[LabelledEmail]) -> None:
    item = emails[0]
    fake = FakeMessages([make_message(ticket_json(item), input_tokens=1000, output_tokens=100)])
    ticks = iter([10.0, 12.5])

    result = extract_one(fake, item, Technique.STRUCTURED, model=MODEL, clock=lambda: next(ticks))

    assert result.outcome is Outcome.OK
    assert result.all_correct
    assert result.summary_ok
    assert result.latency_s == 2.5
    assert result.tally.calls == 1
    assert result.tally.cost_usd == pytest.approx((1000 * 0.10 + 100 * 0.50) / 1_000_000)
    assert fake.calls[0]["model"] == MODEL


def test_repair_turn_sends_back_the_reply_and_the_error(emails: list[LabelledEmail]) -> None:
    item = emails[0]
    first = make_message(
        {"type": "thinking", "thinking": "", "signature": "sig"},
        ticket_json(item, severity="urgent"),
    )
    fake = FakeMessages([first, make_message(ticket_json(item))])

    result = extract_one(fake, item, Technique.PLAIN, model=MODEL, repair=True)

    assert result.outcome is Outcome.OK
    assert result.repaired
    assert result.tally.calls == 2
    _, assistant, user = fake.calls[1]["messages"]
    assert assistant == {"role": "assistant", "content": first.content}  # thinking kept as-is
    assert "severity" in user["content"]
    assert "corrected JSON" in user["content"]


def test_without_repair_the_first_failure_stands(emails: list[LabelledEmail]) -> None:
    fake = FakeMessages([make_message("not json")])
    result = extract_one(fake, emails[0], Technique.PLAIN, model=MODEL)

    assert result.outcome is Outcome.PARSE_ERROR
    assert not result.repaired
    assert result.predicted is None
    assert not result.all_correct
    assert not result.summary_ok


@pytest.mark.parametrize(
    "reply",
    [
        make_message("{", stop_reason="max_tokens"),
        make_message(stop_reason="refusal"),
    ],
    ids=["truncated", "refusal"],
)
def test_repair_is_not_attempted_for_truncation_or_refusal(
    emails: list[LabelledEmail], reply: anthropic.types.Message
) -> None:
    fake = FakeMessages([reply])
    result = extract_one(fake, emails[0], Technique.PLAIN, model=MODEL, repair=True)
    assert len(fake.calls) == 1
    assert result.outcome in (Outcome.TRUNCATED, Outcome.REFUSAL)


def test_failed_repair_keeps_the_second_error(emails: list[LabelledEmail]) -> None:
    fake = FakeMessages([make_message("nope"), make_message("still nope")])
    result = extract_one(fake, emails[0], Technique.PLAIN, model=MODEL, repair=True)
    assert result.outcome is Outcome.PARSE_ERROR
    assert not result.repaired
    assert result.tally.calls == 2


def test_transient_api_error_is_recorded_for_that_item(emails: list[LabelledEmail]) -> None:
    fake = FakeMessages([anthropic.APIConnectionError(request=REQUEST)])
    result = extract_one(fake, emails[0], Technique.PLAIN, model=MODEL, repair=True)

    assert result.outcome is Outcome.API_ERROR
    assert "APIConnectionError" in result.error
    assert result.tally.calls == 0  # nothing billed


def test_configuration_errors_stop_the_run(emails: list[LabelledEmail]) -> None:
    response = httpx2.Response(401, request=REQUEST)
    fake = FakeMessages([anthropic.AuthenticationError("bad key", response=response, body=None)])
    with pytest.raises(anthropic.AuthenticationError):
        extract_one(fake, emails[0], Technique.PLAIN, model=MODEL)


def test_run_all_and_summarise_compare_the_techniques(emails: list[LabelledEmail]) -> None:
    items = emails[:4]
    results = run_all(
        answer_key(items), items, [Technique.PLAIN, Technique.STRUCTURED], model=MODEL, workers=3
    )

    assert [(r.technique, r.id) for r in results] == [
        (t, i.id) for t in (Technique.PLAIN, Technique.STRUCTURED) for i in items
    ]
    plain, structured = summarise(results)
    assert plain.valid == 4
    assert plain.cleaned == 4  # every plain reply came in a markdown fence
    assert plain.accuracy["severity"] == 0.75  # t01 was wrong
    assert plain.all_correct == 0.75
    assert structured.cleaned == 0
    assert structured.all_correct == 1.0
    assert structured.cost_per_1k == pytest.approx((900 * 0.10 + 60 * 0.50) / 1_000_000 * 1000)


def test_cli_writes_the_report_and_raw_rows(
    emails: list[LabelledEmail], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "results.md"
    code = main(
        ["--limit", "3", "--out", str(out), "--workers", "2"],
        api=answer_key(emails),
        settings=Settings(model=MODEL),
    )

    assert code == 0
    report = out.read_text()
    assert "| Metric | plain | fewshot | structured |" in report
    assert "| Valid output (parsed + schema) | 3/3 | 3/3 | 3/3 |" in report
    assert "| t01 | plain | severity | P1 | P4 |" in report
    rows = [json.loads(line) for line in out.with_suffix(".jsonl").read_text().splitlines()]
    assert len(rows) == 9
    assert "Total spend this run" in capsys.readouterr().out


def test_report_lists_failed_outputs_and_says_none_when_clean(
    emails: list[LabelledEmail],
) -> None:
    fake = FakeMessages([make_message("no | json here"), make_message(ticket_json(emails[1]))])
    results = [
        extract_one(fake, emails[0], Technique.PLAIN, model=MODEL),
        extract_one(fake, emails[1], Technique.PLAIN, model=MODEL),
    ]

    report = render(summarise(results), results, header="h")

    assert "| Parse errors | 1 |" in report
    assert "| t01 | plain | parse_error | not valid JSON" in report
    assert "## Wrong values\n\nNone." in report
