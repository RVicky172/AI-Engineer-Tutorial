from pathlib import Path
from typing import Any

import pytest
from anthropic.types import Message
from llm_common.fake import FakeMessages, make_message, tool_use_block

from tool_design.args import ToolName
from tool_design.dataset import Case, Scenario, load_jsonl

DATA = Path(__file__).resolve().parents[1] / "data"
MODEL = "claude-haiku-5-5"

# A complete, valid argument set per tool. Tests override single fields from it.
VALID_ARGS: dict[str, dict[str, str]] = {
    "get_ticket": {"number": "INC0012345"},
    "search_kb": {"query": "vpn gateway unreachable"},
    "restart_service": {
        "service": "vpn-gateway",
        "ticket_number": "INC0012345",
        "reason": "Gateway failing health checks",
    },
    "add_comment": {"ticket_number": "INC0012346", "text": "Done.", "visibility": "internal"},
    "escalate": {"ticket_number": "INC0012345", "group": "network", "reason": "Gateway problem"},
}


@pytest.fixture(scope="session")
def cases() -> list[Case]:
    return load_jsonl(DATA / "requests.jsonl", Case)


@pytest.fixture(scope="session")
def parallel() -> list[Case]:
    return load_jsonl(DATA / "parallel.jsonl", Case)


@pytest.fixture(scope="session")
def scenarios() -> list[Scenario]:
    return load_jsonl(DATA / "recovery.jsonl", Scenario)


def args_for(case: Case, tool: ToolName) -> dict[str, str]:
    return {**VALID_ARGS[tool], **case.expected_args.get(tool, {})}


def answer_key(cases: list[Case]) -> FakeMessages:
    """A fake model that answers each request with its label. On v1 it makes two typical
    mistakes: a01 picks restart_service (the 'restart' trap) and c11 sends free text
    ('networking') where v2's enum would force 'network'."""
    by_request = {c.request: c for c in cases}

    def respond(request: dict[str, Any]) -> Message:
        content = request["messages"][0]["content"]
        case = next(c for r, c in by_request.items() if r in content)
        v1 = request["tools"][0]["description"] == "Get a ticket."
        restart: list[ToolName] = ["restart_service"]
        tools = restart if v1 and case.id == "a01" else case.expected_tools
        blocks: list[str | dict[str, Any]] = []
        for tool in tools:
            args = args_for(case, tool)
            if v1 and case.id == "c11":
                args = {**args, "group": "networking"}
            blocks.append(tool_use_block(tool, args))
        if not blocks:
            blocks = ["Could you tell me the incident number?"]
        return make_message(*blocks, input_tokens=1200, output_tokens=80)

    return FakeMessages(respond)
