import json
from pathlib import Path
from typing import Any

from anthropic.types import Message
from llm_common.fake import FakeMessages, make_message

from regression.cases import Case, load_suite
from regression.checks import FieldEquals, FieldIn

LAB = Path(__file__).resolve().parents[1]
SUITE = load_suite(LAB / "evals" / "cases.yaml")
SAFE_REPLY = "Thanks, we are on it. If you suspect a compromise, disconnect from the network."


def expected(case: Case, field: str) -> str:
    for check in case.checks:
        if isinstance(check, FieldEquals) and check.field == field:
            return check.value
        if isinstance(check, FieldIn) and check.field == field:
            return check.values[0]
    raise KeyError(f"{case.id} pins no {field}")


def answer(case: Case, **overrides: str) -> str:
    data = {
        "category": expected(case, "category"),
        "priority": expected(case, "priority"),
        "reply": SAFE_REPLY,
    }
    return json.dumps({**data, **overrides})


def oracle(broken: dict[str, dict[str, str]] | None = None) -> FakeMessages:
    """A fake model that gives every case its labelled answer, except the overrides in
    `broken` (case id -> fields to change)."""
    broken = broken or {}

    def respond(request: dict[str, Any]) -> Message:
        content = request["messages"][0]["content"]
        case = next(c for c in SUITE.cases if c.input in content)
        return make_message(answer(case, **broken.get(case.id, {})), output_tokens=200)

    return FakeMessages(respond)
