"""Run every case N times against one prompt version and apply its checks.

There is no temperature=0 here: the current API rejects sampling parameters, and even when they
existed, temperature 0 never guaranteed identical outputs. Repeats are how you measure
consistency: a case that passes 2 of 3 runs is flaky, and flaky is a finding, not noise."""

from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

import anthropic
from anthropic.types import Usage
from llm_common import MessagesAPI, UsageTally, text_of

from regression.cases import Case, Suite
from regression.checks import Check, CheckResult, Output, run_check
from regression.prompts import Prompt

FATAL_ERRORS = (
    anthropic.AuthenticationError,
    anthropic.PermissionDeniedError,
    anthropic.NotFoundError,
    anthropic.BadRequestError,
)


class Status(StrEnum):
    PASS = "pass"  # noqa: S105 (a test status, not a password)
    FLAKY = "flaky"  # passed some runs, failed others
    FAIL = "fail"


def build_request(
    prompt: Prompt, case_input: str, *, model: str, effort: str = "low", max_tokens: int = 2048
) -> dict[str, Any]:
    return {
        "model": model,
        "max_tokens": max_tokens,
        "system": [{"type": "text", "text": prompt.text, "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": f"<ticket>\n{case_input}\n</ticket>"}],
        "output_config": {"effort": effort},
    }


@dataclass
class RunResult:
    checks: list[CheckResult] = field(default_factory=list)
    text: str = ""
    error: str = ""  # the call failed or the reply was unusable (refusal, truncation)
    usage: Usage | None = None

    @property
    def passed(self) -> bool:
        return not self.error and all(c.passed for c in self.checks)

    @property
    def failures(self) -> list[str]:
        if self.error:
            return [self.error]
        return [f"{c.check}: {c.detail}" for c in self.checks if not c.passed]


def run_once(api: MessagesAPI, request: dict[str, Any], checks: Sequence[Check]) -> RunResult:
    try:
        reply = api.create(**request)
    except FATAL_ERRORS:
        raise
    except anthropic.APIError as exc:
        return RunResult(error=f"{type(exc).__name__}: {exc}")
    text = text_of(reply).strip()
    if reply.stop_reason in ("refusal", "max_tokens"):
        return RunResult(text=text, error=f"stop_reason={reply.stop_reason}", usage=reply.usage)
    output = Output(text=text, output_tokens=reply.usage.output_tokens)
    return RunResult(checks=[run_check(c, output) for c in checks], text=text, usage=reply.usage)


@dataclass
class CaseRun:
    case: Case
    runs: list[RunResult]

    @property
    def passes(self) -> int:
        return sum(r.passed for r in self.runs)

    @property
    def status(self) -> Status:
        if self.passes == len(self.runs):
            return Status.PASS
        return Status.FAIL if self.passes == 0 else Status.FLAKY

    @property
    def failure_summary(self) -> str:
        """Each distinct failure once, with how many runs hit it."""
        counts: dict[str, int] = {}
        for run in self.runs:
            for failure in run.failures:
                counts[failure] = counts.get(failure, 0) + 1
        return "; ".join(f"{f} ({n}/{len(self.runs)})" for f, n in counts.items())


def run_case(
    api: MessagesAPI,
    suite: Suite,
    case: Case,
    prompt: Prompt,
    *,
    model: str,
    repeats: int = 3,
    effort: str = "low",
    max_tokens: int = 2048,
) -> CaseRun:
    request = build_request(prompt, case.input, model=model, effort=effort, max_tokens=max_tokens)
    checks = suite.checks_for(case)
    with ThreadPoolExecutor(max_workers=repeats) as pool:
        runs = list(pool.map(lambda _: run_once(api, request, checks), range(repeats)))
    return CaseRun(case, runs)


@dataclass
class SuiteRun:
    task: str
    prompt: Prompt
    model: str
    effort: str
    repeats: int
    cases: list[CaseRun]
    started: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def tally(self) -> UsageTally:
        tally = UsageTally(model=self.model)
        for case in self.cases:
            for run in case.runs:
                if run.usage is not None:
                    tally.add(run.usage)
        return tally

    def count(self, status: Status) -> int:
        return sum(c.status is status for c in self.cases)


def run_suite(
    api: MessagesAPI,
    suite: Suite,
    prompt: Prompt,
    *,
    model: str,
    repeats: int = 3,
    effort: str = "low",
    max_tokens: int = 2048,
) -> SuiteRun:
    cases = [
        run_case(
            api,
            suite,
            case,
            prompt,
            model=model,
            repeats=repeats,
            effort=effort,
            max_tokens=max_tokens,
        )
        for case in suite.cases
    ]
    return SuiteRun(suite.task, prompt, model, effort, repeats, cases)
