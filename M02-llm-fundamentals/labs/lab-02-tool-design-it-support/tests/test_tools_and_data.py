import re
from typing import get_args

import pytest
from llm_common.fake import make_message, real_sdk_messages

from tests.conftest import VALID_ARGS
from tool_design.args import ARGS, TOOL_NAMES, Group, Service
from tool_design.backend import TICKETS
from tool_design.dataset import Case, Scenario
from tool_design.selection import build_request
from tool_design.toolsets import V1, V2_DESCRIPTIONS, Version, tools_for, v2_tools


def test_v1_and_v2_differ_only_in_how_tools_are_described() -> None:
    v1, v2 = tools_for(Version.V1), tools_for(Version.V2)
    assert [t["name"] for t in v1] == [t["name"] for t in v2] == list(TOOL_NAMES)
    for a, b in zip(v1, v2, strict=True):
        assert a["input_schema"]["properties"].keys() == b["input_schema"]["properties"].keys()
        assert a["input_schema"]["required"] == b["input_schema"]["required"]


def test_v1_is_the_quick_first_draft() -> None:
    for tool in V1:
        assert len(tool["description"]) < 30
        assert "strict" not in tool
        props = tool["input_schema"]["properties"].values()
        assert all(p == {"type": "string"} for p in props)  # no enums, no formats


def test_v2_is_strict_and_says_when_not_to_use_each_tool() -> None:
    for tool in v2_tools():
        schema = tool["input_schema"]
        assert tool["strict"] is True
        assert schema["additionalProperties"] is False
        assert "Do NOT use" in tool["description"]
        # constraints strict can't enforce are moved into descriptions, so the model reads them
        assert "pattern" not in str(schema.keys())
    props = {t["name"]: t["input_schema"]["properties"] for t in v2_tools()}
    assert props["restart_service"]["service"]["enum"] == list(get_args(Service))
    assert props["escalate"]["group"]["enum"] == list(get_args(Group))
    assert "INC0012345" in props["get_ticket"]["number"]["description"]


def test_escalate_description_explains_every_group() -> None:
    for group in get_args(Group):
        assert group in V2_DESCRIPTIONS["escalate"]


def test_v2_descriptions_only_point_to_tools_that_exist() -> None:
    for text in V2_DESCRIPTIONS.values():
        for named in re.findall(r"use (\w+_\w+)", text):
            assert named in TOOL_NAMES


@pytest.mark.parametrize("version", list(Version))
def test_requests_follow_current_api_rules(version: Version) -> None:
    req = build_request(version, "hello", model="m")
    assert not {"temperature", "top_p", "top_k", "tool_choice"} & req.keys()
    assert req["messages"] == [{"role": "user", "content": "<request>\nhello\n</request>"}]
    assert req["system"][0]["cache_control"] == {"type": "ephemeral"}


@pytest.mark.parametrize("version", list(Version))
def test_the_real_sdk_accepts_and_sends_each_toolset(version: Version) -> None:
    api, sent = real_sdk_messages(make_message("ok"))
    api.create(**build_request(version, "hello", model="m"))
    tools = sent[0]["tools"]
    assert len(tools) == 5
    assert all(t.get("strict") is (True if version is Version.V2 else None) for t in tools)


def test_valid_args_fixture_satisfies_every_contract() -> None:
    for name, model in ARGS.items():
        model.model_validate(VALID_ARGS[name])


def _check_expected_args(case: Case) -> None:
    for tool, values in case.expected_args.items():
        assert tool in case.expected_tools
        ARGS[tool].model_validate({**VALID_ARGS[tool], **values})


def test_request_set_is_balanced_and_labels_are_valid(cases: list[Case]) -> None:
    assert len(cases) == 25
    assert len({c.id for c in cases}) == 25
    categories = [c.category for c in cases]
    assert categories.count("ambiguous") >= 5
    assert categories.count("no_tool") >= 5
    for tool in TOOL_NAMES:
        assert sum(tool in c.expected_tools for c in cases) >= 3, tool
    for c in cases:
        _check_expected_args(c)
        assert c.why


def test_every_incident_in_the_requests_exists_in_the_fake_desk(
    cases: list[Case], parallel: list[Case]
) -> None:
    for c in [*cases, *parallel]:
        for number in re.findall(r"INC\d{7}", c.request):
            assert number in TICKETS, (c.id, number)


def test_parallel_cases_each_need_two_tools(parallel: list[Case]) -> None:
    assert len(parallel) == 3
    for c in parallel:
        assert c.category == "parallel"
        assert len(c.expected_tools) == 2
        _check_expected_args(c)


def test_recovery_scenarios_expect_valid_calls(scenarios: list[Scenario]) -> None:
    assert len({s.id for s in scenarios}) == len(scenarios) == 6
    for s in scenarios:
        for want in s.expect:
            ARGS[want.name].model_validate({**VALID_ARGS[want.name], **want.args})
        assert s.expect or s.forbid_writes  # every scenario has a checkable success condition
