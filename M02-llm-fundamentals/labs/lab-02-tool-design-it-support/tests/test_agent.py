from pathlib import Path
from typing import Any

import anthropic
import httpx2
import pytest
from llm_common import Settings
from llm_common.fake import FakeMessages, make_message, tool_use_block

from tests.conftest import MODEL, VALID_ARGS
from tool_design.agent import run_recovery, run_scenario
from tool_design.backend import ErrorStyle
from tool_design.cli import main
from tool_design.dataset import Scenario
from tool_design.report import render_recovery

REQUEST = httpx2.Request("POST", "https://api.example.test/v1/messages")
FROZEN_RESTART = VALID_ARGS["restart_service"] | {
    "service": "erp-app",
    "ticket_number": "INC0012347",
}
ERP_ESCALATION = VALID_ARGS["escalate"] | {"ticket_number": "INC0012347", "group": "erp-support"}


def by_id(scenarios: list[Scenario], id_: str) -> Scenario:
    return next(s for s in scenarios if s.id == id_)


def test_recovers_from_a_blocked_restart_by_escalating(scenarios: list[Scenario]) -> None:
    first = make_message(
        {"type": "thinking", "thinking": "", "signature": "sig"},
        tool_use_block("restart_service", FROZEN_RESTART, id="toolu_a"),
    )
    fake = FakeMessages(
        [
            first,
            make_message(tool_use_block("escalate", ERP_ESCALATION, id="toolu_b")),
            make_message("Restart is frozen, so I escalated INC0012347 to ERP support."),
        ]
    )

    result = run_scenario(fake, by_id(scenarios, "r01"), ErrorStyle.ACTIONABLE, model=MODEL)

    assert result.success
    assert (result.stop, result.steps, result.errors_seen) == ("end_turn", 3, 1)
    assert result.tally.calls == 3
    # turn 2 sends back the assistant turn unchanged, then the error as a tool_result
    _, assistant, tool_turn = fake.calls[1]["messages"]
    assert assistant == {"role": "assistant", "content": first.content}
    [block] = tool_turn["content"]
    assert block["tool_use_id"] == "toolu_a"
    assert block["is_error"] is True
    assert "group=erp-support" in block["content"]
    assert len(fake.calls[2]["messages"]) == 5  # the history is a copy per call, not shared


def test_successful_results_carry_no_is_error_flag(scenarios: list[Scenario]) -> None:
    fake = FakeMessages(
        [
            make_message(tool_use_block("escalate", VALID_ARGS["escalate"])),
            make_message("Done."),
        ]
    )
    result = run_scenario(fake, by_id(scenarios, "r06"), ErrorStyle.TERSE, model=MODEL)
    assert result.success
    assert "is_error" not in fake.calls[1]["messages"][2]["content"][0]


def test_parallel_results_go_back_in_one_user_message(scenarios: list[Scenario]) -> None:
    fake = FakeMessages(
        [
            make_message(
                tool_use_block("get_ticket", {"number": "INC0012345"}, id="t1"),
                tool_use_block("search_kb", VALID_ARGS["search_kb"], id="t2"),
            ),
            make_message("Here you go."),
        ]
    )
    run_scenario(fake, by_id(scenarios, "r06"), ErrorStyle.TERSE, model=MODEL)
    last = fake.calls[1]["messages"][-1]
    assert last["role"] == "user"
    assert [b["tool_use_id"] for b in last["content"]] == ["t1", "t2"]


def test_repeating_a_failing_call_is_looping(scenarios: list[Scenario]) -> None:
    retry = make_message(tool_use_block("restart_service", FROZEN_RESTART))
    fake = FakeMessages([retry, retry, make_message("Still failing, sorry.")])

    result = run_scenario(fake, by_id(scenarios, "r01"), ErrorStyle.TERSE, model=MODEL)

    assert result.looping
    assert not result.success
    assert [m.name for m in result.missing] == ["escalate"]


def test_too_many_calls_to_one_tool_is_looping(scenarios: list[Scenario]) -> None:
    r03 = by_id(scenarios, "r03")  # max 2 get_ticket calls
    numbers = ["INC0099999", "INC0099998", "INC0099997"]
    fake = FakeMessages(
        [make_message(tool_use_block("get_ticket", {"number": n})) for n in numbers]
        + [make_message("Not found.")]
    )
    result = run_scenario(fake, r03, ErrorStyle.TERSE, model=MODEL)
    assert result.looping
    assert not result.success


def test_step_limit_stops_a_runaway_agent(scenarios: list[Scenario]) -> None:
    def always_search(_: dict[str, Any]) -> anthropic.types.Message:
        return make_message(tool_use_block("search_kb", {"query": "sso password"}))

    result = run_scenario(
        FakeMessages(always_search),
        by_id(scenarios, "r04"),
        ErrorStyle.ACTIONABLE,
        model=MODEL,
        max_steps=3,
    )
    assert (result.stop, result.steps) == ("max_steps", 3)
    assert not result.success


def test_forbidden_write_fails_the_scenario(scenarios: list[Scenario]) -> None:
    r03 = by_id(scenarios, "r03")
    fake = FakeMessages(
        [
            make_message(tool_use_block("add_comment", VALID_ARGS["add_comment"])),
            make_message("I added a note to another ticket instead."),
        ]
    )
    assert not run_scenario(fake, r03, ErrorStyle.TERSE, model=MODEL).success


@pytest.mark.parametrize(
    ("script", "stop"),
    [
        ([anthropic.APIConnectionError(request=REQUEST)], "api_error"),
        ([make_message(stop_reason="refusal")], "refusal"),
    ],
)
def test_api_errors_and_refusals_end_the_scenario(
    scenarios: list[Scenario], script: list[Any], stop: str
) -> None:
    result = run_scenario(FakeMessages(script), scenarios[0], ErrorStyle.TERSE, model=MODEL)
    assert result.stop == stop
    assert not result.success


def test_configuration_errors_stop_the_run(scenarios: list[Scenario]) -> None:
    response = httpx2.Response(401, request=REQUEST)
    fake = FakeMessages([anthropic.AuthenticationError("bad key", response=response, body=None)])
    with pytest.raises(anthropic.AuthenticationError):
        run_scenario(fake, scenarios[0], ErrorStyle.TERSE, model=MODEL)


def _polite_model(request: dict[str, Any]) -> anthropic.types.Message:
    """Calls escalate once, then stops. Good enough to exercise the reporting path."""
    if len(request["messages"]) == 1:
        return make_message(tool_use_block("escalate", VALID_ARGS["escalate"]))
    return make_message("Escalated.")


def test_recovery_report_compares_styles(scenarios: list[Scenario]) -> None:
    results = run_recovery(
        FakeMessages(_polite_model), scenarios[-1:], list(ErrorStyle), model=MODEL
    )
    report = render_recovery(results, header="h")

    assert "| Metric | terse | actionable |" in report
    assert "| Recovered (success) | 1/1 | 1/1 |" in report
    assert "### r06 · terse" in report
    assert "1. `escalate(" in report


def test_cli_recover_writes_report_and_rows(tmp_path: Path) -> None:
    out = tmp_path / "recovery.md"
    code = main(
        ["recover", "--limit", "2", "--out", str(out)],
        api=FakeMessages(_polite_model),
        settings=Settings(model=MODEL),
    )
    assert code == 0
    assert "| Recovered (success) |" in out.read_text()
    assert len(out.with_suffix(".jsonl").read_text().splitlines()) == 4
