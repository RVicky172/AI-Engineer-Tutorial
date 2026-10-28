import argparse
import json
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from llm_common import MessagesAPI, Settings, make_messages_api

from tool_design.agent import run_recovery
from tool_design.backend import ErrorStyle
from tool_design.dataset import Case, Scenario, load_jsonl
from tool_design.report import render_recovery, render_selection
from tool_design.selection import run_all, summarise
from tool_design.toolsets import Version

LAB = Path(__file__).resolve().parents[2]


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="python -m tool_design",
        description="Lab 02 experiments: tool selection and error recovery.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--limit", type=int, help="only the first N cases (smoke test)")
    common.add_argument("--effort", default="low", choices=["low", "medium", "high", "xhigh"])
    common.add_argument("--max-tokens", type=int, default=4096)

    sel = sub.add_parser("select", parents=[common], help="tool selection: v1 vs v2")
    sel.add_argument("--versions", default="v1,v2")
    sel.add_argument("--workers", type=int, default=4)
    sel.add_argument("--data", type=Path, default=LAB / "data" / "requests.jsonl")
    sel.add_argument("--out", type=Path, default=LAB / "results.md")

    rec = sub.add_parser("recover", parents=[common], help="error recovery: terse vs actionable")
    rec.add_argument("--styles", default="terse,actionable")
    rec.add_argument("--data", type=Path, default=LAB / "data" / "recovery.jsonl")
    rec.add_argument("--out", type=Path, default=LAB / "recovery.md")
    return p.parse_args(argv)


def main(
    argv: Sequence[str] | None = None,
    *,
    api: MessagesAPI | None = None,
    settings: Settings | None = None,
) -> int:
    args = parse_args(argv)
    settings = settings or Settings.from_env()
    api = api or make_messages_api(settings)
    model = settings.api_model_id
    header = (
        f"Model: `{model}` ({settings.provider}) · effort: {args.effort} · "
        f"data: `{args.data.name}` · run: {datetime.now(UTC):%Y-%m-%d %H:%M} UTC"
    )
    opts = {"model": model, "effort": args.effort, "max_tokens": args.max_tokens}

    if args.command == "select":
        cases = load_jsonl(args.data, Case)[: args.limit]
        versions = [Version(v.strip()) for v in args.versions.split(",")]
        print(f"{len(cases)} requests x {len(versions)} toolsets on {model} ...")
        results = run_all(api, cases, versions, workers=args.workers, **opts)
        summaries = summarise(results)
        args.out.write_text(render_selection(summaries, results, header=header), encoding="utf-8")
        rows = [json.dumps(r.to_json()) for r in results]
        for s in summaries:
            print(
                f"{s.version}: selection {s.accuracy:.0%}  invalid args {s.invalid_calls}/"
                f"{s.calls}  ${s.cost_per_1k:.2f}/1k requests"
            )
        spend = sum(s.tally.cost_usd for s in summaries)
    else:
        scenarios = load_jsonl(args.data, Scenario)[: args.limit]
        styles = [ErrorStyle(s.strip()) for s in args.styles.split(",")]
        print(f"{len(scenarios)} scenarios x {len(styles)} error styles on {model} ...")
        recovered = run_recovery(api, scenarios, styles, **opts)
        args.out.write_text(render_recovery(recovered, header=header), encoding="utf-8")
        rows = [
            json.dumps(
                {
                    "id": r.scenario.id,
                    "style": str(r.style),
                    "success": r.success,
                    "stop": r.stop,
                    "calls": [
                        {"name": c.name, "input": c.input, "is_error": c.outcome.is_error}
                        for c in r.calls
                    ],
                    "final_text": r.final_text,
                    "cost_usd": round(r.tally.cost_usd, 6),
                }
            )
            for r in recovered
        ]
        for style in styles:
            mine = [r for r in recovered if r.style is style]
            print(f"{style}: recovered {sum(r.success for r in mine)}/{len(mine)}")
        spend = sum(r.tally.cost_usd for r in recovered)

    args.out.with_suffix(".jsonl").write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"Total spend this run: ${spend:.4f}. Report: {args.out}")
    return 0
