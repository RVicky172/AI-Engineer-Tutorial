import json
from pathlib import Path
from typing import Any

import pytest
from anthropic.types import Message
from llm_common.fake import FakeMessages, make_message

from extraction.runner import load_emails
from extraction.schema import LabelledEmail

DATA = Path(__file__).resolve().parents[1] / "data"
MODEL = "claude-haiku-5-5"


@pytest.fixture(scope="session")
def emails() -> list[LabelledEmail]:
    return load_emails(DATA / "tickets.jsonl")


@pytest.fixture(scope="session")
def fewshot() -> list[LabelledEmail]:
    return load_emails(DATA / "fewshot.jsonl")


def ticket_json(item: LabelledEmail, **overrides: str) -> str:
    return json.dumps({**item.expected.model_dump(), **overrides})


def answer_key(items: list[LabelledEmail]) -> FakeMessages:
    """A fake model that 'reads' the email and answers with its label. The plain technique
    wraps JSON in a markdown fence (as real models often do) and gets one severity wrong."""
    by_email = {item.email: item for item in items}

    def respond(request: dict[str, Any]) -> Message:
        content = request["messages"][0]["content"]
        item = next(i for e, i in by_email.items() if e in content)
        if "format" in request["output_config"]:
            return make_message(ticket_json(item), input_tokens=900, output_tokens=60)
        if "<examples>" in request["system"][0]["text"]:
            return make_message(ticket_json(item), input_tokens=1500, output_tokens=60)
        wrong = {"severity": "P4"} if item.id == "t01" else {}
        return make_message(
            f"```json\n{ticket_json(item, **wrong)}\n```", input_tokens=800, output_tokens=80
        )

    return FakeMessages(respond)
