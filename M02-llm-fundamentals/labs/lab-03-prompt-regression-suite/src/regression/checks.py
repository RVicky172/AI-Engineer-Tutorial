"""Deterministic checks on one model output. No LLM judge: every check is cheap, exact and
explainable, which is what a gate that runs on every prompt change needs."""

import json
from dataclasses import dataclass
from functools import cached_property
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class _Check(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class JsonValid(_Check):
    type: Literal["json_valid"] = "json_valid"


class FieldEquals(_Check):
    type: Literal["field_equals"] = "field_equals"
    field: str
    value: str


class FieldIn(_Check):
    """For labels where two answers are defensible. Every use makes the suite easier to pass."""

    type: Literal["field_in"] = "field_in"
    field: str
    values: list[str]


class Contains(_Check):
    """Case-insensitive substring, in one JSON field or (without `field`) in the whole text."""

    type: Literal["contains"] = "contains"
    value: str
    field: str | None = None


class NotContains(_Check):
    type: Literal["not_contains"] = "not_contains"
    value: str
    field: str | None = None


class MaxTokens(_Check):
    """Billed output tokens, which include thinking. A cost guard, not a length check."""

    type: Literal["max_tokens"] = "max_tokens"
    value: int = Field(gt=0)


Check = Annotated[
    JsonValid | FieldEquals | FieldIn | Contains | NotContains | MaxTokens,
    Field(discriminator="type"),
]


@dataclass(frozen=True)
class Output:
    text: str
    output_tokens: int

    @cached_property
    def data(self) -> dict[str, Any] | None:
        """Strict: the whole reply must be one JSON object. A code fence around it fails, since
        the program that consumes this output would fail too."""
        try:
            value = json.loads(self.text)
        except json.JSONDecodeError:
            return None
        return value if isinstance(value, dict) else None


@dataclass(frozen=True)
class CheckResult:
    check: str
    passed: bool
    detail: str = ""


def describe(check: Check) -> str:
    match check:
        case JsonValid():
            return "json_valid"
        case FieldEquals(field=f, value=v):
            return f"field_equals({f}={v})"
        case FieldIn(field=f, values=vs):
            return f"field_in({f} in {'|'.join(vs)})"
        case Contains(value=v, field=f) | NotContains(value=v, field=f):
            return f"{check.type}({f or 'text'} ~ {v!r})"
        case MaxTokens(value=v):
            return f"max_tokens(<= {v})"


def _field(output: Output, name: str) -> tuple[str | None, str]:
    """(value, why it's missing)."""
    if output.data is None:
        return None, "output is not a JSON object"
    if name not in output.data:
        return None, f"no field {name!r}"
    return str(output.data[name]), ""


def _haystack(output: Output, name: str | None) -> tuple[str | None, str]:
    return (output.text, "") if name is None else _field(output, name)


def run_check(check: Check, output: Output) -> CheckResult:
    label = describe(check)
    match check:
        case JsonValid():
            ok = output.data is not None
            return CheckResult(label, ok, "" if ok else f"not a JSON object: {output.text[:80]!r}")
        case FieldEquals(field=name, value=want):
            got, why = _field(output, name)
            if got is None:
                return CheckResult(label, False, why)
            return CheckResult(label, got == want, "" if got == want else f"got {got!r}")
        case FieldIn(field=name, values=allowed):
            got, why = _field(output, name)
            if got is None:
                return CheckResult(label, False, why)
            return CheckResult(label, got in allowed, "" if got in allowed else f"got {got!r}")
        case Contains(value=needle, field=name) | NotContains(value=needle, field=name):
            text, why = _haystack(output, name)
            if text is None:
                return CheckResult(label, False, why)
            found = needle.casefold() in text.casefold()
            ok = found if isinstance(check, Contains) else not found
            return CheckResult(label, ok, "" if ok else ("missing" if not found else "present"))
        case MaxTokens(value=limit):
            ok = output.output_tokens <= limit
            return CheckResult(label, ok, "" if ok else f"used {output.output_tokens}")
