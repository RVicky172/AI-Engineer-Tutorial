from collections.abc import Callable, Sequence

from extraction.parsing import Outcome
from extraction.runner import SCORED_FIELDS, ItemResult, TechniqueSummary


def _pct(x: float) -> str:
    return f"{x:.0%}"


def render(
    summaries: Sequence[TechniqueSummary],
    results: Sequence[ItemResult],
    *,
    header: str,
) -> str:
    """Metrics as rows, techniques as columns: the comparison reads left to right."""
    rows: list[tuple[str, Callable[[TechniqueSummary], str]]] = [
        ("Valid output (parsed + schema)", lambda s: f"{s.valid}/{s.n}"),
        ("Needed cleanup (fences / prose)", lambda s: str(s.cleaned)),
        ("Parse errors", lambda s: str(s.outcomes[Outcome.PARSE_ERROR])),
        ("Schema errors", lambda s: str(s.outcomes[Outcome.SCHEMA_ERROR])),
        ("Truncated (max_tokens)", lambda s: str(s.outcomes[Outcome.TRUNCATED])),
        ("Refusals", lambda s: str(s.outcomes[Outcome.REFUSAL])),
        ("API errors", lambda s: str(s.outcomes[Outcome.API_ERROR])),
        ("Fixed by repair turn", lambda s: str(s.repaired)),
        *[(f"{f} accuracy", (lambda s, f=f: _pct(s.accuracy[f]))) for f in SCORED_FIELDS],
        ("All three fields correct", lambda s: _pct(s.all_correct)),
        ("Summary <= 20 words", lambda s: _pct(s.summary_ok)),
        ("Avg input tokens / email", lambda s: f"{s.tally.input_tokens / s.n:.0f}"),
        ("Avg output tokens / email", lambda s: f"{s.tally.output_tokens / s.n:.0f}"),
        ("  of which thinking", lambda s: f"{s.tally.thinking_tokens / s.n:.0f}"),
        ("Cache read tokens (total)", lambda s: str(s.tally.cache_read_tokens)),
        ("Calls (incl. repairs)", lambda s: str(s.tally.calls)),
        ("Cost per 1k emails (USD)", lambda s: f"${s.cost_per_1k:.2f}"),
        ("p50 latency (s)", lambda s: f"{s.p50_latency_s:.1f}"),
    ]
    names = [str(s.technique) for s in summaries]
    lines = [
        "# Lab 01 results: one extraction task, three techniques",
        "",
        header,
        "",
        "| Metric | " + " | ".join(names) + " |",
        "|---|" + "---|" * len(names),
    ]
    lines += [f"| {label} | " + " | ".join(fn(s) for s in summaries) + " |" for label, fn in rows]

    mistakes = [
        (r, f)
        for r in results
        for f in SCORED_FIELDS
        if r.predicted is not None and not r.correct(f)
    ]
    failures = [r for r in results if r.predicted is None]
    lines += ["", "## Wrong values", ""]
    if mistakes:
        lines += ["| Email | Technique | Field | Expected | Got |", "|---|---|---|---|---|"]
        lines += [
            f"| {r.id} | {r.technique} | {f} | {getattr(r.expected, f)} | "
            f"{getattr(r.predicted, f)} |"
            for r, f in mistakes
        ]
    else:
        lines.append("None.")
    lines += ["", "## Failed outputs", ""]
    if failures:
        lines += ["| Email | Technique | Outcome | Error |", "|---|---|---|---|"]
        lines += [
            f"| {r.id} | {r.technique} | {r.outcome} | {r.error.replace('|', '/')[:150]} |"
            for r in failures
        ]
    else:
        lines.append("None.")
    lines += [
        "",
        "## Conclusion",
        "",
        "_Write three sentences: which technique you would ship, why (accuracy vs. failure rate "
        "vs. cost), and the one change that would improve it most._",
        "",
    ]
    return "\n".join(lines)
