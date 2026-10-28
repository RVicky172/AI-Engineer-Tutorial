import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from llm_common import MessagesAPI, Settings, make_messages_api

from regression.cases import load_suite
from regression.prompts import PromptStore
from regression.report import diff, write_report
from regression.runner import Status, run_suite

LAB = Path(__file__).resolve().parents[2]
TASK = "triage"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="python -m regression",
        description="Prompt regression suite (pytest evals/ is the gate).",
    )
    p.add_argument("--prompts", type=Path, default=LAB / "prompts")
    p.add_argument("--reports", type=Path, default=LAB / "reports")
    sub = p.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="run the suite for one prompt version and write its report")
    run.add_argument("--version", help="prompt version (default: CURRENT)")
    run.add_argument("--repeats", type=int, default=3)
    run.add_argument("--effort", default="low", choices=["low", "medium", "high", "xhigh"])
    run.add_argument("--cases", type=Path, default=LAB / "evals" / "cases.yaml")

    d = sub.add_parser("diff", help="compare two versions' saved reports")
    d.add_argument("old")
    d.add_argument("new")

    sub.add_parser("versions", help="list prompt versions and CURRENT")
    return p.parse_args(argv)


def main(
    argv: Sequence[str] | None = None,
    *,
    api: MessagesAPI | None = None,
    settings: Settings | None = None,
) -> int:
    args = parse_args(argv)
    store = PromptStore(args.prompts)

    if args.command == "versions":
        current = store.current(TASK)
        for v in store.versions(TASK):
            prompt = store.load(TASK, v)
            print(f"{'*' if v == current else ' '} {v}  {prompt.sha}  {prompt.note}")
        return 0

    if args.command == "diff":
        old, new = (
            json.loads((args.reports / f"{TASK}-{v}.json").read_text(encoding="utf-8"))
            for v in (args.old, args.new)
        )
        out = args.reports / f"diff-{TASK}-{args.old}-{args.new}.md"
        out.write_text(diff(old, new), encoding="utf-8")
        print(out.read_text(encoding="utf-8"))
        return 0

    settings = settings or Settings.from_env()
    api = api or make_messages_api(settings)
    suite = load_suite(args.cases)
    prompt = store.load(suite.task, args.version)
    print(f"{len(suite.cases)} cases x {args.repeats} on {settings.api_model_id}, {prompt.version}")
    result = run_suite(
        api,
        suite,
        prompt,
        model=settings.api_model_id,
        repeats=args.repeats,
        effort=args.effort,
    )
    report = write_report(result, args.reports)
    print(
        f"{result.count(Status.PASS)} pass, {result.count(Status.FLAKY)} flaky, "
        f"{result.count(Status.FAIL)} fail. ${result.tally.cost_usd:.4f}. Report: {report}"
    )
    return 0 if result.count(Status.PASS) == len(result.cases) else 1
