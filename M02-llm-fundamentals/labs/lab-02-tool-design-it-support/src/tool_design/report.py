from collections.abc import Callable, Sequence

from tool_design.agent import RecoveryResult
from tool_design.backend import ErrorStyle
from tool_design.selection import CaseResult, Outcome, VersionSummary


def _pct(x: float | None) -> str:
    return "n/a" if x is None else f"{x:.0%}"


def _cell(text: str, limit: int = 120) -> str:
    """Markdown table cells can't hold pipes or newlines."""
    flat = " ".join(text.replace("|", "/").split())
    return flat if len(flat) <= limit else flat[: limit - 3] + "..."


def _tools(names: Sequence[str]) -> str:
    return ", ".join(names) if names else "(none)"


def _choice(r: CaseResult) -> str:
    if r.selection_correct:
        return "ok"
    return _tools(r.chosen) if r.outcome is Outcome.OK else str(r.outcome)


def render_selection(
    summaries: Sequence[VersionSummary], results: Sequence[CaseResult], *, header: str
) -> str:
    rows: list[tuple[str, Callable[[VersionSummary], str]]] = [
        ("Tool selection accuracy", lambda s: _pct(s.accuracy)),
        *[
            (
                f"  {category}",
                lambda s, c=category: "{}/{}".format(*s.by_category.get(c, (0, 0))),
            )
            for category in dict.fromkeys(c for s in summaries for c in s.by_category)
        ],
        ("Called a tool when none was needed", lambda s: str(s.unneeded_calls)),
        ("Called nothing when a tool was needed", lambda s: str(s.missed_calls)),
        ("Tool calls made", lambda s: str(s.calls)),
        ("Argument validity (calls passing the contract)", lambda s: _pct(s.arg_validity)),
        ("Argument values correct (when tool right)", lambda s: _pct(s.args_correct)),
        ("Refusals / truncations / API errors", lambda s: str(s.failures)),
        ("Avg input tokens / request", lambda s: f"{s.tally.input_tokens / s.n:.0f}"),
        ("Cache read tokens (total)", lambda s: str(s.tally.cache_read_tokens)),
        ("Avg output tokens / request", lambda s: f"{s.tally.output_tokens / s.n:.0f}"),
        ("Cost per 1k requests (USD)", lambda s: f"${s.cost_per_1k:.2f}"),
        ("p50 latency (s)", lambda s: f"{s.p50_latency_s:.1f}"),
    ]
    names = [str(s.version) for s in summaries]
    lines = [
        "# Lab 02 results: tool selection, v1 vs v2 definitions",
        "",
        header,
        "",
        "| Metric | " + " | ".join(names) + " |",
        "|---|" + "---|" * len(names),
        *[f"| {label} | " + " | ".join(fn(s) for s in summaries) + " |" for label, fn in rows],
    ]

    by_case: dict[str, dict[str, CaseResult]] = {}
    for r in results:
        by_case.setdefault(r.case.id, {})[str(r.version)] = r
    misses = [rs for rs in by_case.values() if any(not r.selection_correct for r in rs.values())]
    lines += ["", "## Wrong tool choices", ""]
    if misses:
        lines += [
            "| Case | Category | Request | Expected | " + " | ".join(names) + " |",
            "|---|---|---|---|" + "---|" * len(names),
        ]
        for rs in misses:
            case = next(iter(rs.values())).case
            got = [_choice(rs[n]) if n in rs else "" for n in names]
            lines.append(
                f"| {case.id} | {case.category} | {_cell(case.request, 70)} | "
                f"{_tools(case.expected_tools)} | " + " | ".join(got) + " |"
            )
    else:
        lines.append("None.")

    invalid = [(r, c) for r in results for c in r.calls if not c.valid]
    lines += ["", "## Invalid arguments", ""]
    if invalid:
        lines += ["| Case | Version | Tool | Input | Problem |", "|---|---|---|---|---|"]
        lines += [
            f"| {r.case.id} | {r.version} | {c.name} | `{_cell(str(c.input), 80)}` | "
            f"{_cell(c.error)} |"
            for r, c in invalid
        ]
    else:
        lines.append("None.")
    lines += [
        "",
        "## Description changes that made the biggest difference",
        "",
        "_Read the 'Wrong tool choices' table. For each v1 miss that v2 fixed, name the sentence "
        "in the v2 description (or the enum) that fixed it. List the top three._",
        "",
    ]
    return "\n".join(lines)


def render_recovery(results: Sequence[RecoveryResult], *, header: str) -> str:
    styles = list(dict.fromkeys(r.style for r in results))

    def of(style: ErrorStyle) -> list[RecoveryResult]:
        return [r for r in results if r.style is style]

    def avg(style: ErrorStyle, value: Callable[[RecoveryResult], float]) -> str:
        rows = of(style)
        return f"{sum(value(r) for r in rows) / len(rows):.1f}" if rows else "n/a"

    rows: list[tuple[str, Callable[[ErrorStyle], str]]] = [
        ("Recovered (success)", lambda s: f"{sum(r.success for r in of(s))}/{len(of(s))}"),
        ("Looping (repeated failing call)", lambda s: str(sum(r.looping for r in of(s)))),
        ("Hit the step limit", lambda s: str(sum(r.stop == "max_steps" for r in of(s)))),
        ("Avg model calls / scenario", lambda s: avg(s, lambda r: r.steps)),
        ("Avg tool errors / scenario", lambda s: avg(s, lambda r: r.errors_seen)),
        ("Total cost (USD)", lambda s: f"${sum(r.tally.cost_usd for r in of(s)):.4f}"),
    ]
    lines = [
        "# Lab 02 results: recovering from tool errors",
        "",
        header,
        "",
        "| Metric | " + " | ".join(styles) + " |",
        "|---|" + "---|" * len(styles),
        *[f"| {label} | " + " | ".join(fn(s) for s in styles) + " |" for label, fn in rows],
        "",
        "## Per scenario",
        "",
        "| Scenario | Style | Success | Stop | Calls | Errors | Missing |",
        "|---|---|---|---|---|---|---|",
    ]
    lines += [
        f"| {r.scenario.id} | {r.style} | {'yes' if r.success else 'NO'} | {r.stop} | "
        f"{len(r.calls)} | {r.errors_seen} | "
        f"{_tools([m.name for m in r.missing])} |"
        for r in results
    ]
    lines += ["", "## Transcripts", ""]
    for r in results:
        lines += [f"### {r.scenario.id} · {r.style}", "", f"> {_cell(r.scenario.request, 200)}", ""]
        lines += [
            f"{i}. `{c.name}({_cell(str(c.input), 100)})` -> "
            f"{'**error** ' if c.outcome.is_error else ''}{_cell(c.outcome.content)}"
            for i, c in enumerate(r.calls, 1)
        ]
        lines += ["", f"Final ({r.stop}): {_cell(r.final_text, 300) or '(no text)'}", ""]
    return "\n".join(lines)
