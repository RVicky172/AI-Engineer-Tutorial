import json
from typing import Any, get_args

import pytest
from llm_common.fake import make_message, real_sdk_messages

from extraction.prompts import SYSTEM, Technique, build_request
from extraction.schema import LabelledEmail, Service, Severity

EMAIL = "From: a@acme.example\nSubject: hi\n\nVPN broken"


def all_keys(node: Any) -> set[str]:
    if isinstance(node, dict):
        return set(node) | {k for v in node.values() for k in all_keys(v)}
    if isinstance(node, list):
        return {k for v in node for k in all_keys(v)}
    return set()


def test_dataset_is_complete_and_well_formed(emails: list[LabelledEmail]) -> None:
    assert len(emails) == 30
    assert len({e.id for e in emails}) == 30
    # every service and severity appears, so per-class mistakes are visible
    assert {e.expected.service for e in emails} == set(get_args(Service))
    assert {e.expected.severity for e in emails} == set(get_args(Severity))


def test_fewshot_examples_never_leak_into_the_eval_set(
    emails: list[LabelledEmail], fewshot: list[LabelledEmail]
) -> None:
    eval_text = {e.email for e in emails}
    assert len(fewshot) == 3
    assert not any(f.email in eval_text for f in fewshot)


def test_system_prompt_names_every_allowed_value() -> None:
    for value in (*get_args(Service), *get_args(Severity)):
        assert value in SYSTEM


@pytest.mark.parametrize("technique", list(Technique))
def test_every_request_follows_current_api_rules(technique: Technique) -> None:
    req = build_request(technique, EMAIL, model="m", fewshot=[])

    assert not {"temperature", "top_p", "top_k"} & req.keys()  # rejected by the current API
    assert req["messages"][-1]["role"] == "user"  # no assistant prefill (400 on current models)
    assert req["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert req["output_config"]["effort"] == "low"
    assert f"<email>\n{EMAIL}\n</email>" in req["messages"][0]["content"]


def test_fewshot_examples_go_in_the_cacheable_system_prompt(
    fewshot: list[LabelledEmail],
) -> None:
    req = build_request(Technique.FEWSHOT, EMAIL, model="m", fewshot=fewshot)
    system = req["system"][0]["text"]

    assert system.startswith(SYSTEM)
    assert system.count("<example>") == 3
    assert fewshot[1].expected.model_dump_json() in system
    assert "<examples>" not in req["messages"][0]["content"]


def test_structured_request_sends_an_api_ready_schema() -> None:
    req = build_request(Technique.STRUCTURED, EMAIL, model="m")
    fmt = req["output_config"]["format"]
    schema = fmt["schema"]

    assert fmt["type"] == "json_schema"
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == {"service", "severity", "requester", "summary"}
    assert schema["properties"]["service"]["enum"] == list(get_args(Service))
    # Unsupported constraints are moved into descriptions, so the API does NOT enforce them.
    # That's why parse_reply still validates every structured reply with Pydantic.
    assert not {"pattern", "maxLength", "minLength"} & all_keys(schema)
    assert "pattern" in schema["properties"]["requester"]["description"]
    json.dumps(schema)  # serialisable as sent


def test_plain_and_fewshot_ask_for_json_but_structured_does_not() -> None:
    for technique in (Technique.PLAIN, Technique.FEWSHOT):
        req = build_request(technique, EMAIL, model="m")
        assert "Respond with only a JSON object" in req["messages"][0]["content"]
        assert "format" not in req["output_config"]


@pytest.mark.parametrize("technique", list(Technique))
def test_the_real_sdk_accepts_and_sends_each_request(
    technique: Technique, emails: list[LabelledEmail], fewshot: list[LabelledEmail]
) -> None:
    api, sent = real_sdk_messages(make_message("{}"))

    api.create(**build_request(technique, emails[0].email, model="m", fewshot=fewshot))

    body = sent[0]
    assert body["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert ("format" in body["output_config"]) == (technique is Technique.STRUCTURED)
