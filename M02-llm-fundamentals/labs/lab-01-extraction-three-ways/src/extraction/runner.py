import json
import statistics
import time
from collections import Counter
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import anthropic
from anthropic.types import Message
from llm_common import MessagesAPI, UsageTally

from extraction.parsing import Outcome, Parsed, parse_reply
from extraction.prompts import Technique, build_request, repair_message
from extraction.schema import LabelledEmail, Ticket

SCORED_FIELDS = ("service", "severity", "requester")
MAX_SUMMARY_WORDS = 20

# Configuration mistakes: every call would fail the same way, so stop instead of recording
# 90 identical failures. Transient errors (429, 5xx, network) are recorded per item after the
# SDK's own retries.
FATAL_ERRORS = (
    anthropic.AuthenticationError,
    anthropic.PermissionDeniedError,
    anthropic.NotFoundError,
    anthropic.BadRequestError,
)


def load_emails(path: Path) -> list[LabelledEmail]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [LabelledEmail.model_validate_json(line) for line in lines if line.strip()]


@dataclass
class ItemResult:
    id: str
    technique: Technique
    expected: Ticket
    outcome: Outcome
    predicted: Ticket | None = None
    error: str = ""
    cleaned: bool = False
    repaired: bool = False
    latency_s: float = 0.0
    tally: UsageTally = field(default_factory=lambda: UsageTally(model="unknown"))

    def correct(self, name: str) -> bool:
        return self.predicted is not None and getattr(self.predicted, name) == getattr(
            self.expected, name
        )

    @property
    def all_correct(self) -> bool:
        return all(self.correct(name) for name in SCORED_FIELDS)

    @property
    def summary_ok(self) -> bool:
        return self.predicted is not None and len(self.predicted.summary.split()) <= (
            MAX_SUMMARY_WORDS
        )

    def to_json(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "technique": str(self.technique),
            "outcome": str(self.outcome),
            "error": self.error,
            "cleaned": self.cleaned,
            "repaired": self.repaired,
            "expected": self.expected.model_dump(),
            "predicted": self.predicted.model_dump() if self.predicted else None,
            "calls": self.tally.calls,
            "input_tokens": self.tally.input_tokens,
            "output_tokens": self.tally.output_tokens,
            "thinking_tokens": self.tally.thinking_tokens,
            "cost_usd": round(self.tally.cost_usd, 6),
            "latency_s": round(self.latency_s, 3),
        }


def _call(
    api: MessagesAPI, request: dict[str, Any], tally: UsageTally
) -> tuple[Parsed, Message | None]:
    try:
        reply = api.create(**request)
    except FATAL_ERRORS:
        raise
    except anthropic.APIError as exc:
        return Parsed(Outcome.API_ERROR, error=f"{type(exc).__name__}: {exc}"), None
    tally.add(reply.usage)
    return parse_reply(reply), reply


def extract_one(
    api: MessagesAPI,
    item: LabelledEmail,
    technique: Technique,
    *,
    model: str,
    fewshot: Sequence[LabelledEmail] = (),
    effort: str = "low",
    max_tokens: int = 4096,
    repair: bool = False,
    clock: Callable[[], float] = time.perf_counter,
) -> ItemResult:
    request = build_request(
        technique, item.email, model=model, fewshot=fewshot, effort=effort, max_tokens=max_tokens
    )
    tally = UsageTally(model=model)
    start = clock()
    parsed, reply = _call(api, request, tally)
    repaired = False
    if repair and parsed.outcome.repairable and reply is not None:
        # Send the assistant turn back exactly as returned (thinking blocks included).
        request["messages"] = [
            *request["messages"],
            {"role": "assistant", "content": reply.content},
            {"role": "user", "content": repair_message(parsed.error)},
        ]
        parsed, _ = _call(api, request, tally)
        repaired = parsed.outcome is Outcome.OK
    return ItemResult(
        id=item.id,
        technique=technique,
        expected=item.expected,
        outcome=parsed.outcome,
        predicted=parsed.ticket,
        error=parsed.error,
        cleaned=parsed.cleaned,
        repaired=repaired,
        latency_s=clock() - start,
        tally=tally,
    )


def run_all(
    api: MessagesAPI,
    items: Sequence[LabelledEmail],
    techniques: Sequence[Technique],
    *,
    workers: int = 4,
    **kwargs: Any,
) -> list[ItemResult]:
    """Every (technique, email) pair once. Threads, because the SDK client is thread-safe and
    the work is waiting on the network; results come back in a stable order."""
    jobs = [(t, item) for t in techniques for item in items]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(extract_one, api, item, t, **kwargs) for t, item in jobs]
        return [f.result() for f in futures]


@dataclass(frozen=True)
class TechniqueSummary:
    technique: Technique
    n: int
    outcomes: Counter[Outcome]
    cleaned: int
    repaired: int
    accuracy: dict[str, float]
    all_correct: float
    summary_ok: float
    tally: UsageTally
    p50_latency_s: float

    @property
    def valid(self) -> int:
        return self.outcomes[Outcome.OK]

    @property
    def cost_per_1k(self) -> float:
        return self.tally.cost_usd / self.n * 1000 if self.n else 0.0


def summarise(results: Sequence[ItemResult]) -> list[TechniqueSummary]:
    """Failures count as wrong on every field: a parse error is not 'excluded', it's a miss."""
    summaries = []
    for technique in dict.fromkeys(r.technique for r in results):
        rows = [r for r in results if r.technique is technique]
        n = len(rows)
        tally = UsageTally(model=rows[0].tally.model)
        for r in rows:
            tally.merge(r.tally)
        summaries.append(
            TechniqueSummary(
                technique=technique,
                n=n,
                outcomes=Counter(r.outcome for r in rows),
                cleaned=sum(r.cleaned for r in rows),
                repaired=sum(r.repaired for r in rows),
                accuracy={f: sum(r.correct(f) for r in rows) / n for f in SCORED_FIELDS},
                all_correct=sum(r.all_correct for r in rows) / n,
                summary_ok=sum(r.summary_ok for r in rows) / n,
                tally=tally,
                p50_latency_s=statistics.median(r.latency_s for r in rows),
            )
        )
    return summaries


def write_jsonl(results: Sequence[ItemResult], path: Path) -> None:
    path.write_text("".join(json.dumps(r.to_json()) + "\n" for r in results), encoding="utf-8")
