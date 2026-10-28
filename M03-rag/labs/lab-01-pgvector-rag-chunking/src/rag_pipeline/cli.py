import argparse
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psycopg
from llm_common import MessagesAPI, Settings, make_messages_api

from rag_pipeline.pipeline import IngestStats, Mode, Retriever, evaluate, ingest, table_name
from rag_pipeline.report import Run, render
from ragkit.corpus import load_corpus
from ragkit.embedding import Embedder, make_embedder
from ragkit.generation import answer
from ragkit.golden import check_evidence, load_golden
from ragkit.metrics import summarise
from ragkit.store import PgVectorStore, connect

LABS = Path(__file__).resolve().parents[3]
LAB = LABS / "lab-01-pgvector-rag-chunking"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="python -m rag_pipeline", description="M03 Lab 01")
    p.add_argument("--embedder", default="local", choices=["local", "titan", "hash"])
    p.add_argument("--corpus", type=Path, default=LABS / "corpus")
    p.add_argument("--golden", type=Path, default=LABS / "golden.yaml")
    sub = p.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="ingest every size, evaluate every mode, write results.md")
    run.add_argument("--sizes", default="128,256,512")
    run.add_argument("--overlap", type=float, default=0.125, help="fraction of the chunk size")
    run.add_argument("--modes", default="vector,bm25,hybrid")
    run.add_argument("--skip-ingest", action="store_true", help="reuse existing tables")
    run.add_argument("--out", type=Path, default=LAB / "results.md")

    ask = sub.add_parser("ask", help="answer one question with citations (calls the model)")
    ask.add_argument("question")
    ask.add_argument("--size", type=int, default=256)
    ask.add_argument("--mode", default="hybrid", choices=[m.value for m in Mode])
    ask.add_argument("-k", type=int, default=5)

    ans = sub.add_parser("answer-golden", help="answer the golden set (calls the model)")
    ans.add_argument("--size", type=int, default=256)
    ans.add_argument("--mode", default="hybrid", choices=[m.value for m in Mode])
    ans.add_argument("--limit", type=int)
    ans.add_argument("--out", type=Path, default=LAB / "answers.md")
    return p.parse_args(argv)


def main(
    argv: Sequence[str] | None = None,
    *,
    conn: psycopg.Connection[Any] | None = None,
    embedder_factory: Callable[[str], Embedder] = make_embedder,
    api: MessagesAPI | None = None,
    settings: Settings | None = None,
) -> int:
    args = parse_args(argv)
    conn = conn or connect()
    embedder = embedder_factory(args.embedder)
    docs = load_corpus(args.corpus)
    questions = load_golden(args.golden, {d.doc_id for d in docs})
    check_evidence(questions, docs)

    if args.command == "run":
        sizes = [int(s) for s in args.sizes.split(",")]
        modes = [Mode(m) for m in args.modes.split(",")]
        stats: list[IngestStats] = []
        if not args.skip_ingest:
            for size in sizes:
                stats.append(ingest(conn, docs, embedder, size=size, overlap=args.overlap))
                print(f"ingested {size}: {stats[-1].chunks} chunks in {stats[-1].seconds:.1f}s")
        runs: list[Run] = []
        for size in sizes:
            store = PgVectorStore(conn, table_name(embedder, size), embedder.dim)
            retriever = Retriever(store, embedder)
            for mode in modes:
                name = f"{size} {mode}"
                results = evaluate(retriever, questions, mode)
                summary = summarise(name, results)
                runs.append((name, summary, results))
                print(
                    f"{name:<14} recall@5 {summary.recall_at_5:.0%}  "
                    f"evidence@5 {summary.evidence_at_5:.0%}  MRR {summary.mrr:.2f}"
                )
        header = (
            f"Embedder: `{embedder.name}` ({embedder.dim} dims, reads {embedder.max_tokens} "
            f"tokens) · overlap {args.overlap:.0%} · corpus {len(docs)} docs · "
            f"run {datetime.now(UTC):%Y-%m-%d %H:%M} UTC"
        )
        args.out.write_text(render(runs, stats, questions, header=header), encoding="utf-8")
        print(f"Report: {args.out}")
        return 0

    settings = settings or Settings.from_env()
    api = api or make_messages_api(settings)
    retriever = Retriever(
        PgVectorStore(conn, table_name(embedder, args.size), embedder.dim), embedder
    )
    if args.command == "ask":
        hits = retriever.search(args.question, Mode(args.mode), args.k)
        result = answer(api, args.question, hits, model=settings.api_model_id)
        print(result.text, "\n")
        print("Retrieved:", ", ".join(dict.fromkeys(h.doc_id for h in hits)))
        print(
            "Citations ok:",
            result.citations.ok,
            "| not in context:",
            list(result.citations.not_in_context) or "none",
        )
        return 0 if result.citations.ok else 1

    lines = [
        "# Lab 01 answers with citations",
        "",
        f"Model `{settings.api_model_id}` · chunks {args.size} · {args.mode} · top 5",
        "",
    ]
    ok = 0
    selected = questions[: args.limit]
    for q in selected:
        hits = retriever.search(q.question, Mode(args.mode), 5)
        result = answer(api, q.question, hits, model=settings.api_model_id)
        ok += result.citations.ok
        relevant_cited = sorted(set(result.citations.cited) & set(q.relevant))
        lines += [
            f"## {q.id}: {q.question}",
            "",
            result.text,
            "",
            f"- Reference: {q.answer}",
            f"- Cited: {', '.join(result.citations.cited) or 'nothing'} · relevant cited: "
            f"{', '.join(relevant_cited) or 'none'} · citations ok: {result.citations.ok}",
            "",
        ]
    lines.insert(3, f"**Citations valid: {ok}/{len(selected)}**\n")
    args.out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Citations valid {ok}/{len(selected)}. Report: {args.out}")
    return 0
