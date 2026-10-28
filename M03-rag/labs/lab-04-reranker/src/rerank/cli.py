import argparse
import re
import statistics
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psycopg
from llm_common import MessagesAPI, Settings, make_messages_api

from ragkit.corpus import load_corpus
from ragkit.embedding import Embedder, make_embedder
from ragkit.generation import answer
from ragkit.golden import check_evidence, load_golden
from ragkit.retrieval import Mode, Retriever
from ragkit.store import PgVectorStore, build_table, connect
from rerank.experiment import CANDIDATES, compare
from rerank.judge import judge
from rerank.report import render
from rerank.rerankers import Reranker, make_reranker

LABS = Path(__file__).resolve().parents[3]
LAB = LABS / "lab-04-reranker"


def table_name(embedder: Embedder, size: int) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", embedder.name.lower().rsplit("/", 1)[-1]).strip("_")
    return f"l04_{slug}_{size}"[:63]


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="python -m rerank", description="M03 Lab 04")
    p.add_argument("--embedder", default="local", choices=["local", "titan", "hash"])
    p.add_argument(
        "--reranker", default="cross-encoder", choices=["cross-encoder", "bedrock", "lexical"]
    )
    p.add_argument("--bedrock-model-arn", help="for --reranker bedrock")
    p.add_argument("--size", type=int, default=256)
    sub = p.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="retrieval before/after reranking -> results.md")
    run.add_argument("--first-stage", default="vector,hybrid")
    run.add_argument("--out", type=Path, default=LAB / "results.md")
    ans = sub.add_parser("answers", help="answer + judge, before/after (calls the model)")
    ans.add_argument("--first-stage", default="hybrid", choices=[m.value for m in Mode])
    ans.add_argument("--limit", type=int)
    ans.add_argument("--out", type=Path, default=LAB / "answers.md")
    return p.parse_args(argv)


def main(
    argv: Sequence[str] | None = None,
    *,
    conn: psycopg.Connection[Any] | None = None,
    embedder_factory: Callable[[str], Embedder] = make_embedder,
    reranker_factory: Callable[..., Reranker] = make_reranker,
    api: MessagesAPI | None = None,
    settings: Settings | None = None,
) -> int:
    args = parse_args(argv)
    conn = conn or connect()
    embedder = embedder_factory(args.embedder)
    kwargs = {"model_arn": args.bedrock_model_arn} if args.reranker == "bedrock" else {}
    reranker = reranker_factory(args.reranker, **kwargs)
    docs = load_corpus(LABS / "corpus")
    questions = load_golden(LABS / "golden.yaml", {d.doc_id for d in docs})
    check_evidence(questions, docs)

    if args.command == "run":
        store = build_table(
            conn, docs, embedder, table=table_name(embedder, args.size), size=args.size
        )
        retriever = Retriever(store, embedder)
        comparisons = [
            compare(retriever, reranker, questions, Mode(m)) for m in args.first_stage.split(",")
        ]
        for c in comparisons:
            before, after = c.summaries()
            print(
                f"{after.name:<18} evidence@5 {before.evidence_at_5:.0%} -> "
                f"{after.evidence_at_5:.0%}  MRR {before.mrr:.2f} -> {after.mrr:.2f}  "
                f"+{c.p50_ms:.0f} ms p50"
            )
        header = (
            f"Embedder `{embedder.name}` · reranker `{reranker.name}` · {args.size}-token chunks "
            f"· {CANDIDATES} candidates -> top 5 · run {datetime.now(UTC):%Y-%m-%d %H:%M} UTC"
        )
        args.out.write_text(render(comparisons, questions, header=header), encoding="utf-8")
        print(f"Report: {args.out}")
        return 0

    settings = settings or Settings.from_env()
    api = api or make_messages_api(settings)
    model = settings.api_model_id
    retriever = Retriever(
        PgVectorStore(conn, table_name(embedder, args.size), embedder.dim), embedder
    )
    mode = Mode(args.first_stage)
    rows = ["| Question | Before | After | Judge's reason (after) |", "|---|---|---|---|"]
    scores: dict[str, list[int]] = {"before": [], "after": []}
    for q in questions[: args.limit]:
        candidates = retriever.search(q.question, mode, CANDIDATES)
        contexts = {"before": candidates[:5], "after": reranker.rerank(q.question, candidates, 5)}
        grades = {}
        for label, hits in contexts.items():
            reply = answer(api, q.question, hits, model=model)
            grades[label] = judge(api, q.question, q.answer, reply.text, model=model)
            scores[label].append(grades[label].score)
        reason = grades["after"].reason.replace("|", "/")
        rows.append(f"| {q.id} | {grades['before'].score} | {grades['after'].score} | {reason} |")
    means = {k: statistics.fmean(v) for k, v in scores.items()}
    lines = [
        "# Lab 04 answer quality: judged 1-5 against the reference",
        "",
        f"Answers and judge: `{model}` · first stage {mode} · reranker `{reranker.name}`",
        "",
        f"**Mean score: before {means['before']:.2f} -> after {means['after']:.2f}**",
        "",
        *rows,
        "",
    ]
    args.out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Mean judge score {means['before']:.2f} -> {means['after']:.2f}. Report: {args.out}")
    return 0
