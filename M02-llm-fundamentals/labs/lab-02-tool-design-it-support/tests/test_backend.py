import json

import pytest

from tests.conftest import VALID_ARGS
from tool_design.backend import TICKETS, ErrorStyle, FakeServiceDesk


def test_each_tool_succeeds_with_valid_arguments() -> None:
    desk = FakeServiceDesk()
    for name, args in VALID_ARGS.items():
        assert not desk.execute(name, args).is_error, name
    assert [c.name for c in desk.writes] == ["restart_service", "add_comment", "escalate"]


def test_get_ticket_returns_compact_json_with_the_last_three_comments() -> None:
    desk = FakeServiceDesk()
    for i in range(4):
        desk.execute(
            "add_comment",
            {"ticket_number": "INC0012346", "text": f"note {i}", "visibility": "internal"},
        )
    out = desk.execute("get_ticket", {"number": "INC0012346"})

    assert " " not in out.content.split('"short_description"')[0]  # no indentation
    assert json.loads(out.content)["comments"] == ["note 1", "note 2", "note 3"]


def test_desk_state_is_per_instance() -> None:
    FakeServiceDesk().execute("escalate", VALID_ARGS["escalate"] | {"group": "security"})
    assert TICKETS["INC0012345"]["group"] == "network"


def test_search_kb_ranks_by_keyword_overlap_and_hints_on_no_match() -> None:
    desk = FakeServiceDesk()
    hits = json.loads(desk.execute("search_kb", {"query": "print spooler stuck"}).content)
    assert hits["results"][0]["id"] == "KB0003"
    none = json.loads(desk.execute("search_kb", {"query": "quantum flux"}).content)
    assert none == {"results": [], "hint": "Try fewer, broader keywords."}


@pytest.mark.parametrize(
    ("name", "args", "terse", "actionable"),
    [
        (
            "add_comment",
            VALID_ARGS["add_comment"] | {"ticket_number": "inc12346"},
            "Error 400: invalid input",
            "Did you mean INC0012346?",
        ),
        (
            "get_ticket",
            {"number": "12"},
            "Error 400: invalid input",
            "INC followed by exactly 7 digits",
        ),
        ("get_ticket", {"number": "INC0099999"}, "Error 404", "do not guess another one"),
        (
            "restart_service",
            VALID_ARGS["restart_service"] | {"service": "erp-app", "ticket_number": "INC0012347"},
            "Error 409",
            "escalate with group=erp-support",
        ),
        (
            "add_comment",
            VALID_ARGS["add_comment"] | {"ticket_number": "INC0012349"},
            "Error 409",
            "is Closed",
        ),
        ("escalate", VALID_ARGS["escalate"] | {"group": "networking"}, "Error 400", "group"),
        ("reboot_everything", {}, "Error: unknown tool", "There is no tool named"),
    ],
    ids=["did-you-mean", "bad-number", "not-found", "frozen", "closed", "bad-enum", "unknown"],
)
def test_errors_are_terse_or_actionable(
    name: str, args: dict[str, str], terse: str, actionable: str
) -> None:
    short = FakeServiceDesk(style=ErrorStyle.TERSE).execute(name, args)
    helpful = FakeServiceDesk(style=ErrorStyle.ACTIONABLE).execute(name, args)

    assert short.is_error and helpful.is_error
    assert short.content.startswith(terse)
    assert actionable in helpful.content


def test_did_you_mean_only_suggests_incidents_that_exist() -> None:
    desk = FakeServiceDesk()
    out = desk.execute("get_ticket", {"number": "INC99999"})
    assert out.is_error
    assert "Did you mean" not in out.content


def test_failed_writes_do_not_count_as_writes() -> None:
    desk = FakeServiceDesk()
    desk.execute("add_comment", VALID_ARGS["add_comment"] | {"ticket_number": "INC0012349"})
    assert len(desk.calls) == 1
    assert desk.writes == []


def test_kb_times_out_the_configured_number_of_times_then_recovers() -> None:
    desk = FakeServiceDesk(kb_failures=1)
    first = desk.execute("search_kb", {"query": "sso password"})
    second = desk.execute("search_kb", {"query": "sso password"})

    assert first.is_error and "Retry the same search once" in first.content
    assert not second.is_error
    assert json.loads(second.content)["results"][0]["id"] == "KB0001"


@pytest.mark.parametrize("name", ["restart_service", "add_comment", "escalate"])
def test_writes_to_a_missing_incident_fail(name: str) -> None:
    desk = FakeServiceDesk()
    out = desk.execute(name, VALID_ARGS[name] | {"ticket_number": "INC0099999"})
    assert out.is_error and "No incident INC0099999" in out.content
    assert desk.writes == []
