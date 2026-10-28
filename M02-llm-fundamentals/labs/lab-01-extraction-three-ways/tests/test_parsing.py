import pytest
from llm_common.fake import make_message

from extraction.parsing import Outcome, parse_reply

GOOD = (
    '{"service": "vpn", "severity": "P1", "requester": "Priya.Nair@acme.example", "summary": "x"}'
)


def test_clean_json_parses_and_requester_is_normalised() -> None:
    parsed = parse_reply(make_message(GOOD))

    assert parsed.outcome is Outcome.OK
    assert parsed.ticket is not None
    assert parsed.ticket.requester == "priya.nair@acme.example"
    assert not parsed.cleaned


@pytest.mark.parametrize(
    "text",
    [
        f"```json\n{GOOD}\n```",
        f"```\n{GOOD}\n```",
        f"Here is the extraction:\n{GOOD}\nLet me know if you need more.",
    ],
    ids=["json-fence", "bare-fence", "prose-around"],
)
def test_wrapped_json_parses_but_is_flagged_as_cleaned(text: str) -> None:
    parsed = parse_reply(make_message(text))
    assert parsed.outcome is Outcome.OK
    assert parsed.cleaned


@pytest.mark.parametrize(
    "text",
    ["The service is VPN and severity P1.", "", "{not json at all}"],
    ids=["prose", "empty", "broken-braces"],
)
def test_non_json_is_a_parse_error(text: str) -> None:
    parsed = parse_reply(make_message(text))
    assert parsed.outcome is Outcome.PARSE_ERROR
    assert "not valid JSON" in parsed.error


@pytest.mark.parametrize(
    ("text", "field"),
    [
        (GOOD.replace('"vpn"', '"network"'), "service"),
        (GOOD.replace('"P1"', '"high"'), "severity"),
        (GOOD.replace("Priya.Nair@acme.example", "Priya Nair"), "requester"),
        (GOOD.replace('"x"}', '"x", "confidence": 0.9}'), "confidence"),
        ('{"service": "vpn"}', "severity"),
        ("[1, 2]", "<root>"),
    ],
    ids=["bad-enum", "bad-severity", "not-an-email", "extra-key", "missing-keys", "not-object"],
)
def test_wrong_shape_is_a_schema_error_naming_the_field(text: str, field: str) -> None:
    parsed = parse_reply(make_message(text))
    assert parsed.outcome is Outcome.SCHEMA_ERROR
    assert field in parsed.error


def test_truncated_reply_is_never_parsed_even_if_it_looks_complete() -> None:
    parsed = parse_reply(make_message(GOOD, stop_reason="max_tokens"))
    assert parsed.outcome is Outcome.TRUNCATED
    assert parsed.ticket is None


def test_refusal_records_the_category() -> None:
    msg = make_message(
        stop_reason="refusal",
        stop_details={"type": "refusal", "category": "cyber", "explanation": "declined"},
    )
    parsed = parse_reply(msg)
    assert parsed.outcome is Outcome.REFUSAL
    assert "cyber" in parsed.error


def test_only_format_errors_are_repairable() -> None:
    assert {o for o in Outcome if o.repairable} == {Outcome.PARSE_ERROR, Outcome.SCHEMA_ERROR}
