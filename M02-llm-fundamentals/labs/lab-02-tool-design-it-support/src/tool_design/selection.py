"""Experiment 1: send each request once and score which tools the model picks, and with what
arguments. Nothing is executed: we only read the model's first move."""

import statistics
import time
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

import anthropic
from anthropic.types import Message
from llm_common import MessagesAPI, UsageTally, text_of, tool_uses
from pydantic import ValidationError

from tool_design.args import ARGS
from tool_design.dataset import Case
from tool_design.toolsets import SYSTEM, Version, tools_for

# Configuration mistakes fail every call the same way: stop the run instead of recording them.
FATAL_ERRORS = (
    anthropic.AuthenticationError,
    anthropic.PermissionDeniedError,
    anthropic.NotFoundError,
    anthropic.BadRequestError,
)


class Outcome(StrEnum):
    OK = "ok"
    REFUSAL = "refusal"
    TRUNCATED = "truncated"
    API_ERROR = "api_error"


def wrap_request(text: str) -> str:
    return f"<request>\n{text}\n</request>"


def build_request(
    version: Version,
    request: str,
    *,
    model: str,
    effort: str = "low",
    max_tokens: int = 4096,
) -> dict[str, Any]:
    """tool_choice is left at its default, auto: the model may call nothing, one tool, or several
    in parallel. Forcing a call ("any"/"tool") would make the no-tool cases meaningless, and the
    current Opus/Sonnet models reject it anyway. Tools render before the system prompt, so the
    breakpoint on the system block caches both."""
    return {
        "model": model,
        "max_tokens": max_tokens,
        "tools": tools_for(version),
        "system": [{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": wrap_request(request)}],
        "output_config": {"effort": effort},
    }


@dataclass(frozen=True)
class CallCheck:
    name: str
    input: dict[str, Any]
    error: str = ""  # empty: the arguments satisfy the tool's contract

    @property
    def valid(self) -> bool:
        return not self.error


def check_call(name: str, tool_input: dict[str, Any]) -> CallCheck:
    model = ARGS.get(name)
    if model is None:
        return CallCheck(name, tool_input, error="unknown tool")
    try:
        model.model_validate(tool_input)
    except ValidationError as exc:
        error = "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors())
        return CallCheck(name, tool_input, error=error)
    return CallCheck(name, tool_input)


def same_value(a: object, b: str) -> bool:
    return str(a).strip().casefold() == b.strip().casefold()


@dataclass
class CaseResult:
    case: Case
    version: Version
    outcome: Outcome
    chosen: list[str] = field(default_factory=list)
    calls: list[CallCheck] = field(default_factory=list)
    text: str = ""
    error: str = ""
    latency_s: float = 0.0
    tally: UsageTally = field(default_factory=lambda: UsageTally(model="unknown"))

    @property
    def selection_correct(self) -> bool:
        if self.outcome is not Outcome.OK:
            return False
        accepted = [self.case.expected_tools, *self.case.also_ok]
        return any(sorted(self.chosen) == sorted(ok) for ok in accepted)

    @property
    def args_valid(self) -> bool | None:
        """None when no tool was called: there were no arguments to judge."""
        return all(c.valid for c in self.calls) if self.calls else None

    @property
    def args_correct(self) -> bool | None:
        """Only judged when the right tool was picked and the case pins argument values."""
        if not self.selection_correct or not self.case.expected_args:
            return None
        return all(
            any(
                c.name == tool and all(same_value(c.input.get(k), v) for k, v in want.items())
                for c in self.calls
            )
            for tool, want in self.case.expected_args.items()
        )

    def to_json(self) -> dict[str, Any]:
        return {
            "id": self.case.id,
            "version": str(self.version),
            "category": self.case.category,
            "outcome": str(self.outcome),
            "expected": self.case.expected_tools,
            "chosen": self.chosen,
            "selection_correct": self.selection_correct,
            "args_valid": self.args_valid,
            "args_correct": self.args_correct,
            "calls": [{"name": c.name, "input": c.input, "error": c.error} for c in self.calls],
            "text": self.text,
            "error": self.error,
            "input_tokens": self.tally.input_tokens,
            "output_tokens": self.tally.output_tokens,
            "cost_usd": round(self.tally.cost_usd, 6),
            "latency_s": round(self.latency_s, 3),
        }


def score_reply(case: Case, version: Version, reply: Message) -> CaseResult:
    if reply.stop_reason == "refusal":
        return CaseResult(case, version, Outcome.REFUSAL, error="refused")
    if reply.stop_reason == "max_tokens":
        return CaseResult(case, version, Outcome.TRUNCATED, error="hit max_tokens")
    uses = tool_uses(reply)
    return CaseResult(
        case,
        version,
        Outcome.OK,
        chosen=[u.name for u in uses],
        calls=[check_call(u.name, dict(u.input)) for u in uses],
        text=text_of(reply).strip(),
    )


def run_case(
    api: MessagesAPI,
    case: Case,
    version: Version,
    *,
    model: str,
    effort: str = "low",
    max_tokens: int = 4096,
    clock: Callable[[], float] = time.perf_counter,
) -> CaseResult:
    request = build_request(
        version, case.request, model=model, effort=effort, max_tokens=max_tokens
    )
    tally = UsageTally(model=model)
    start = clock()
    try:
        reply = api.create(**request)
    except FATAL_ERRORS:
        raise
    except anthropic.APIError as exc:
        result = CaseResult(case, version, Outcome.API_ERROR, error=f"{type(exc).__name__}: {exc}")
    else:
        tally.add(reply.usage)
        result = score_reply(case, version, reply)
    result.latency_s = clock() - start
    result.tally = tally
    return result


def run_all(
    api: MessagesAPI,
    cases: Sequence[Case],
    versions: Sequence[Version],
    *,
    workers: int = 4,
    **kwargs: Any,
) -> list[CaseResult]:
    jobs = [(v, c) for v in versions for c in cases]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(run_case, api, c, v, **kwargs) for v, c in jobs]
        return [f.result() for f in futures]


def _rate(flags: Sequence[bool | None]) -> float | None:
    judged = [f for f in flags if f is not None]
    return sum(judged) / len(judged) if judged else None


@dataclass(frozen=True)
class VersionSummary:
    version: Version
    n: int
    accuracy: float
    by_category: dict[str, tuple[int, int]]  # category -> (correct, total)
    calls: int
    invalid_calls: int
    args_correct: float | None
    unneeded_calls: int  # called a tool when the label says none was needed
    missed_calls: int  # called nothing when the label says a tool was needed
    failures: int  # refusals, truncations, API errors
    tally: UsageTally
    p50_latency_s: float

    @property
    def arg_validity(self) -> float | None:
        return (self.calls - self.invalid_calls) / self.calls if self.calls else None

    @property
    def cost_per_1k(self) -> float:
        return self.tally.cost_usd / self.n * 1000 if self.n else 0.0


def summarise(results: Sequence[CaseResult]) -> list[VersionSummary]:
    summaries = []
    for version in dict.fromkeys(r.version for r in results):
        rows = [r for r in results if r.version is version]
        tally = UsageTally(model=rows[0].tally.model)
        for r in rows:
            tally.merge(r.tally)
        categories = dict.fromkeys(r.case.category for r in rows)
        ok = [r for r in rows if r.outcome is Outcome.OK]
        summaries.append(
            VersionSummary(
                version=version,
                n=len(rows),
                accuracy=sum(r.selection_correct for r in rows) / len(rows),
                by_category={
                    c: (
                        sum(r.selection_correct for r in rows if r.case.category == c),
                        sum(r.case.category == c for r in rows),
                    )
                    for c in categories
                },
                calls=sum(len(r.calls) for r in rows),
                invalid_calls=sum(not c.valid for r in rows for c in r.calls),
                args_correct=_rate([r.args_correct for r in rows]),
                unneeded_calls=sum(bool(r.calls) for r in ok if not r.case.expected_tools),
                missed_calls=sum(not r.calls for r in ok if r.case.expected_tools),
                failures=len(rows) - len(ok),
                tally=tally,
                p50_latency_s=statistics.median(r.latency_s for r in rows),
            )
        )
    return summaries
