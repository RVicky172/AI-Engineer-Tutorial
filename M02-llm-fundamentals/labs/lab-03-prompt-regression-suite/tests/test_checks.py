import pytest

from regression.checks import (
    Check,
    Contains,
    FieldEquals,
    FieldIn,
    JsonValid,
    MaxTokens,
    NotContains,
    Output,
    describe,
    run_check,
)

GOOD = Output('{"category": "network", "priority": "P1", "reply": "Please Disconnect."}', 300)


@pytest.mark.parametrize(
    ("check", "label"),
    [
        (JsonValid(), "json_valid"),
        (FieldEquals(field="priority", value="P1"), "field_equals(priority=P1)"),
        (FieldIn(field="priority", values=["P1", "P2"]), "field_in(priority in P1|P2)"),
        (Contains(value="disconnect", field="reply"), "contains(reply ~ 'disconnect')"),
        (NotContains(value="PWNED"), "not_contains(text ~ 'PWNED')"),
        (MaxTokens(value=500), "max_tokens(<= 500)"),
    ],
)
def test_every_check_passes_on_a_good_output(check: Check, label: str) -> None:
    result = run_check(check, GOOD)
    assert result.passed, result.detail
    assert result.check == describe(check) == label


@pytest.mark.parametrize(
    ("check", "detail"),
    [
        (FieldEquals(field="priority", value="P2"), "got 'P1'"),
        (FieldIn(field="category", values=["identity"]), "got 'network'"),
        (Contains(value="restart", field="reply"), "missing"),
        (NotContains(value="disconnect", field="reply"), "present"),
        (MaxTokens(value=299), "used 300"),
        (FieldEquals(field="owner", value="x"), "no field 'owner'"),
    ],
)
def test_failing_checks_explain_why(check: Check, detail: str) -> None:
    result = run_check(check, GOOD)
    assert not result.passed
    assert result.detail == detail


@pytest.mark.parametrize(
    "text",
    ['```json\n{"priority": "P1"}\n```', '["P1"]', "P1", ""],
    ids=["fenced", "array", "prose", "empty"],
)
def test_json_checks_are_strict(text: str) -> None:
    out = Output(text, 10)
    assert out.data is None
    assert not run_check(JsonValid(), out).passed
    field_check = run_check(FieldEquals(field="priority", value="P1"), out)
    assert field_check.detail == "output is not a JSON object"
    assert not run_check(FieldIn(field="priority", values=["P1"]), out).passed
    assert not run_check(Contains(value="P1", field="priority"), out).passed


def test_text_checks_without_a_field_look_at_the_whole_reply() -> None:
    out = Output("Sure! ```json {}```", 10)
    assert run_check(Contains(value="SURE"), out).passed  # case-insensitive
    assert not run_check(NotContains(value="json"), out).passed
