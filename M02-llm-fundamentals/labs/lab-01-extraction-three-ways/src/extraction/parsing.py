import json
import re
from dataclasses import dataclass
from enum import StrEnum

from anthropic.types import Message
from llm_common import text_of
from pydantic import ValidationError

from extraction.schema import Ticket

FENCE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)


class Outcome(StrEnum):
    OK = "ok"
    PARSE_ERROR = "parse_error"  # not JSON at all
    SCHEMA_ERROR = "schema_error"  # JSON, but wrong keys/values
    TRUNCATED = "truncated"  # hit max_tokens: output is cut off
    REFUSAL = "refusal"  # safety classifier declined
    API_ERROR = "api_error"  # the call itself failed

    @property
    def repairable(self) -> bool:
        """Only format mistakes are worth a repair turn. Re-asking after a refusal or a
        truncation just pays for the same failure twice."""
        return self in (Outcome.PARSE_ERROR, Outcome.SCHEMA_ERROR)


@dataclass(frozen=True)
class Parsed:
    outcome: Outcome
    ticket: Ticket | None = None
    error: str = ""
    cleaned: bool = False  # JSON only parsed after stripping fences/prose


def _loads_lenient(text: str) -> tuple[object, bool]:
    """Strict json.loads first; then strip a ``` fence; then take the outermost {...}.
    `cleaned` is reported separately: a technique that needs cleanup is fragile."""
    try:
        return json.loads(text), False
    except json.JSONDecodeError:
        pass
    stripped = text.strip()
    if match := FENCE.match(stripped):
        stripped = match.group(1)
    start, end = stripped.find("{"), stripped.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("no JSON object found in the reply")
    return json.loads(stripped[start : end + 1]), True


def summarise_validation_error(exc: ValidationError) -> str:
    return "; ".join(
        f"{'.'.join(str(p) for p in err['loc']) or '<root>'}: {err['msg']}" for err in exc.errors()
    )


def parse_reply(message: Message) -> Parsed:
    if message.stop_reason == "refusal":
        category = message.stop_details.category if message.stop_details else None
        return Parsed(Outcome.REFUSAL, error=f"refused (category={category})")
    if message.stop_reason == "max_tokens":
        return Parsed(Outcome.TRUNCATED, error="hit max_tokens before finishing")
    text = text_of(message)
    try:
        data, cleaned = _loads_lenient(text)
    except ValueError as exc:  # JSONDecodeError is a ValueError
        return Parsed(Outcome.PARSE_ERROR, error=f"not valid JSON ({exc})")
    try:
        ticket = Ticket.model_validate(data)
    except ValidationError as exc:
        return Parsed(Outcome.SCHEMA_ERROR, error=summarise_validation_error(exc), cleaned=cleaned)
    return Parsed(Outcome.OK, ticket=ticket, cleaned=cleaned)
