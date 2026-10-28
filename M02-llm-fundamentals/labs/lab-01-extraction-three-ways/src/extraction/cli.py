import argparse
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from llm_common import MessagesAPI, Settings, make_messages_api

from extraction.prompts import Technique
from extraction.report import render
from extraction.runner import load_emails, run_all, summarise, write_jsonl

LAB = Path(__file__).resolve().parents[2]


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="python -m extraction", description="Run the three extraction techniques."
    )
    p.add_argument(
        "--techniques",
        default=",".join(Technique),
        help="comma-separated: plain,fewshot,structured (default: all)",
    )
    p.add_argument("--limit", type=int, help="only the first N emails (smoke test: --limit 3)")
    p.add_argument("--repair", action="store_true", help="one repair turn on parse/schema errors")
    p.add_argument("--effort", default="low", choices=["low", "medium", "high", "xhigh", "max"])
    p.add_argument("--max-tokens", type=int, default=4096)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--data", type=Path, default=LAB / "data" / "tickets.jsonl")
    p.add_argument("--out", type=Path, default=LAB / "results.md")
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
    techniques = [Technique(t.strip()) for t in args.techniques.split(",")]
    items = load_emails(args.data)[: args.limit]
    fewshot = load_emails(args.data.parent / "fewshot.jsonl")

    print(f"{len(items)} emails x {len(techniques)} techniques on {settings.api_model_id} ...")
    results = run_all(
        api,
        items,
        techniques,
        workers=args.workers,
        model=settings.api_model_id,
        fewshot=fewshot,
        effort=args.effort,
        max_tokens=args.max_tokens,
        repair=args.repair,
    )
    summaries = summarise(results)
    header = (
        f"Model: `{settings.api_model_id}` ({settings.provider}) · effort: {args.effort} · "
        f"emails: {len(items)} · repair turn: {'on' if args.repair else 'off'} · "
        f"run: {datetime.now(UTC):%Y-%m-%d %H:%M} UTC"
    )
    args.out.write_text(render(summaries, results, header=header), encoding="utf-8")
    write_jsonl(results, args.out.with_suffix(".jsonl"))

    for s in summaries:
        print(
            f"{s.technique:<11} valid {s.valid}/{s.n}  all-correct {s.all_correct:.0%}  "
            f"${s.cost_per_1k:.2f}/1k emails"
        )
    total = sum(s.tally.cost_usd for s in summaries)
    print(f"Total spend this run: ${total:.4f}. Report: {args.out}")
    return 0
