import argparse
import os
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from kb_lab.infra import Clients, KnowledgeBaseLab, State
from kb_lab.prepare import prepare
from kb_lab.query import evaluate, retrieve_and_generate
from ragkit.corpus import load_corpus
from ragkit.golden import load_golden

LABS = Path(__file__).resolve().parents[3]
LAB = LABS / "lab-02-bedrock-knowledge-bases"
PREFIX = "m03-kb-lab"

COST_WARNING = """\
This creates BILLABLE resources in AWS account {account}, region {region}:
  - S3 bucket {prefix}-docs-{account} (the corpus, under 1 MB)
  - S3 Vectors bucket + index (storage and queries are billed)
  - Bedrock Knowledge Base + data source, and one ingestion job (Titan embedding tokens)
  - IAM role {prefix}-kb-role
Delete everything afterwards with: python -m kb_lab down
Re-run with --yes to proceed."""


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="python -m kb_lab", description="M03 Lab 02")
    p.add_argument("--region", default=os.environ.get("AWS_REGION"))
    p.add_argument("--state", type=Path, default=LAB / "kb_state.json")
    sub = p.add_subparsers(dest="command", required=True)
    pr = sub.add_parser("prepare", help="write upload files + .metadata.json sidecars (local)")
    pr.add_argument("--out", type=Path, default=LAB / "build" / "kb-upload")
    up = sub.add_parser("up", help="create bucket, vector store, role, KB; ingest (BILLABLE)")
    up.add_argument("--yes", action="store_true", help="confirm creating billable resources")
    sub.add_parser("eval", help="golden set recall@5 against the KB (billed per query)")
    ask = sub.add_parser("ask", help="RetrieveAndGenerate one question (billed)")
    ask.add_argument("question")
    ask.add_argument("--model-arn", required=True, help="a Claude model or inference profile ARN")
    ask.add_argument("--groups", help="comma-separated: answer as a user in these groups")
    sub.add_parser("down", help="delete everything, then list what remains")
    sub.add_parser("status", help="list resources with the lab prefix")
    return p.parse_args(argv)


def main(
    argv: Sequence[str] | None = None,
    *,
    session_factory: Callable[[str | None], Any] | None = None,
) -> int:
    args = parse_args(argv)
    docs = load_corpus(LABS / "corpus")
    if args.command == "prepare":
        files = prepare(docs, args.out)
        print(f"wrote {len(files)} files ({len(docs)} docs + sidecars) to {args.out}")
        return 0

    if session_factory is None:
        import boto3

        def session_factory(region: str | None) -> Any:
            return boto3.Session(region_name=region)

    session = session_factory(args.region)
    region = session.region_name
    account = session.client("sts").get_caller_identity()["Account"]
    state = State.load(args.state) if args.state.exists() else State(PREFIX, region, account)
    lab = KnowledgeBaseLab(Clients.from_session(session), state, args.state)

    if args.command == "up":
        if not args.yes:
            print(COST_WARNING.format(account=account, region=region, prefix=PREFIX))
            return 2
        out = LAB / "build" / "kb-upload"
        files = prepare(docs, out)
        lab.create_bucket(files, out)
        lab.create_vector_store()
        lab.create_role()
        lab.create_knowledge_base()
        result = lab.ingest()
        print(f"Knowledge base {state.kb_id}: ingestion {result['status']}")
        print(f"statistics: {result['statistics']}")
        for reason in result["failureReasons"]:
            print(f"  failure: {reason}")
        return 0 if result["status"] == "COMPLETE" else 1

    if args.command in ("down", "status"):
        if args.command == "down":
            lab.down()
            if args.state.exists():
                args.state.unlink()
        left = lab.remaining()
        print("Remaining resources with prefix", PREFIX + ":", "none" if not left else "")
        for item in left:
            print("  ", item)
        return 1 if (args.command == "down" and left) else 0

    if not state.kb_id:
        print("No knowledge base in the state file: run `python -m kb_lab up --yes` first.")
        return 2
    runtime = session.client("bedrock-agent-runtime")
    if args.command == "eval":
        questions = load_golden(LABS / "golden.yaml", {d.doc_id for d in docs})
        for as_askers in (False, True):
            s = evaluate(runtime, state.kb_id, questions, as_askers=as_askers)
            print(
                f"{s.name:<28} recall@5 {s.recall_at_5:.0%}  evidence@5 "
                f"{s.evidence_at_5:.0%}  MRR {s.mrr:.2f}  p50 {s.p50_latency_ms:.0f} ms"
            )
        return 0
    groups = args.groups.split(",") if args.groups else None
    text, cited = retrieve_and_generate(
        runtime, state.kb_id, args.model_arn, args.question, groups=groups
    )
    print(text, "\n\nCited:", ", ".join(cited) or "nothing")
    return 0
