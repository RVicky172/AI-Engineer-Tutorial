"""Reports are written as JSON (the record, diffable later) and Markdown (for people). The
Markdown is rendered from the JSON, so the two can't disagree."""

import json
from pathlib import Path
from typing import Any

from regression.runner import Status, SuiteRun

RANK = {Status.FAIL: 0, Status.FLAKY: 1, Status.PASS: 2}


def to_json(run: SuiteRun) -> dict[str, Any]:
    tally = run.tally
    return {
        "task": run.task,
        "version": run.prompt.version,
        "prompt_sha": run.prompt.sha,
        "note": run.prompt.note,
        "model": run.model,
        "effort": run.effort,
        "repeats": run.repeats,
        "started": run.started.isoformat(timespec="seconds"),
        "totals": {s.value: run.count(s) for s in Status},
        "cost_usd": round(tally.cost_usd, 6),
        "output_tokens": tally.output_tokens,
        "cases": {
            c.case.id: {
                "status": str(c.status),
                "passes": c.passes,
                "runs": len(c.runs),
                "failures": c.failure_summary,
                "sample_output": c.runs[0].text[:300] if c.runs else "",
            }
            for c in run.cases
        },
    }


def _cell(text: str) -> str:
    return " ".join(text.replace("|", "/").split())


def render_markdown(data: dict[str, Any]) -> str:
    totals = data["totals"]
    lines = [
        f"# Regression report: {data['task']} {data['version']}",
        "",
        f"Prompt `{data['version']}` (sha `{data['prompt_sha']}`): {data['note']}",
        "",
        f"Model: `{data['model']}` · effort: {data['effort']} · repeats: {data['repeats']} · "
        f"run: {data['started']} · cost: ${data['cost_usd']:.4f}",
        "",
        f"**{totals['pass']} pass · {totals['flaky']} flaky · {totals['fail']} fail** "
        f"of {len(data['cases'])} cases",
        "",
        "| Case | Status | Runs passed | Failed checks |",
        "|---|---|---|---|",
    ]
    lines += [
        f"| {case_id} | {c['status'].upper()} | {c['passes']}/{c['runs']} | "
        f"{_cell(c['failures'])} |"
        for case_id, c in data["cases"].items()
    ]
    return "\n".join(lines) + "\n"


def write_report(run: SuiteRun, out_dir: Path) -> Path:
    """reports/<task>-<version>.json and .md; returns the .md path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    data = to_json(run)
    stem = out_dir / f"{run.task}-{run.prompt.version}"
    stem.with_suffix(".json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    md = stem.with_suffix(".md")
    md.write_text(render_markdown(data), encoding="utf-8")
    return md


def diff(old: dict[str, Any], new: dict[str, Any]) -> str:
    """Per-case status change between two reports. Regressions first: they block the release."""
    ids = list(dict.fromkeys([*old["cases"], *new["cases"]]))
    rows: dict[str, list[str]] = {"regressed": [], "fixed": [], "unchanged": [], "new/removed": []}
    for case_id in ids:
        a, b = old["cases"].get(case_id), new["cases"].get(case_id)
        if a is None or b is None:
            kind = "new/removed"
        else:
            delta = RANK[Status(b["status"])] - RANK[Status(a["status"])]
            kind = "regressed" if delta < 0 else "fixed" if delta > 0 else "unchanged"
        before = f"{a['status']} {a['passes']}/{a['runs']}" if a else "-"
        after = f"{b['status']} {b['passes']}/{b['runs']}" if b else "-"
        detail = _cell(b["failures"]) if b else ""
        rows[kind].append(f"| {case_id} | {kind} | {before} | {after} | {detail} |")

    lines = [
        f"# Prompt diff: {old['task']} {old['version']} -> {new['version']}",
        "",
        f"- {old['version']}: {old['note']}",
        f"- {new['version']}: {new['note']}",
        "",
        "| | " + old["version"] + " | " + new["version"] + " |",
        "|---|---|---|",
        *[f"| {s} | {old['totals'][s]} | {new['totals'][s]} |" for s in ("pass", "flaky", "fail")],
        f"| cost (USD) | ${old['cost_usd']:.4f} | ${new['cost_usd']:.4f} |",
        "",
        f"**{len(rows['regressed'])} regressed · {len(rows['fixed'])} fixed · "
        f"{len(rows['unchanged'])} unchanged**",
        "",
        "| Case | Change | Before | After | Failures after |",
        "|---|---|---|---|---|",
    ]
    for kind in rows:
        lines += rows[kind]
    return "\n".join(lines) + "\n"
