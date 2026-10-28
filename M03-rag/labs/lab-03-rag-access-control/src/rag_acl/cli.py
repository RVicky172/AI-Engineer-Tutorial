import argparse
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psycopg
from llm_common import MessagesAPI, Settings, make_messages_api

from rag_acl.attacks import ATTACKS
from rag_acl.evaluate import golden_as_askers, leak_scan
from rag_acl.identity import DIRECTORY, User
from rag_acl.report import render
from rag_acl.retriever import (
    Mode,
    PostFilterRetriever,
    SecureRetriever,
    UnfilteredRetriever,
    ingest,
    table_name,
)
from rag_acl.service import ask
from ragkit.corpus import load_corpus
from ragkit.embedding import Embedder, make_embedder
from ragkit.golden import load_golden
from ragkit.metrics import Summary
from ragkit.store import PgVectorStore, connect

LABS = Path(__file__).resolve().parents[3]
LAB = LABS / "lab-03-rag-access-control"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="python -m rag_acl", description="M03 Lab 03")
    p.add_argument("--embedder", default="local", choices=["local", "titan", "hash"])
    p.add_argument("--size", type=int, default=256)
    sub = p.add_subparsers(dest="command", required=True)
    ev = sub.add_parser("evaluate", help="ingest, scan for leaks, measure recall: results.md")
    ev.add_argument("--out", type=Path, default=LAB / "results.md")
    a = sub.add_parser("ask", help="answer as an authenticated user (calls the model)")
    a.add_argument("--token", required=True, help=f"one of {', '.join(DIRECTORY)}")
    a.add_argument("question")
    return p.parse_args(argv)


def _avg_returned(retriever: SecureRetriever, questions: Sequence[Any]) -> float:
    counts = [
        len(retriever.search(User("asker", frozenset(q.groups)), q.question, Mode.HYBRID, 5))
        for q in questions
    ]
    return sum(counts) / len(counts)


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
    docs = load_corpus(LABS / "corpus")

    if args.command == "evaluate":
        store = ingest(conn, docs, embedder, size=args.size)
        retrievers = {
            "secure (filter in the query)": SecureRetriever(store, embedder),
            "post-filter (top k, then drop)": PostFilterRetriever(store, embedder),
            "no access control (Lab 01)": UnfilteredRetriever(store, embedder),
        }
        scans = [(name, leak_scan(r, docs)) for name, r in retrievers.items()]
        questions = load_golden(LABS / "golden.yaml", {d.doc_id for d in docs})
        golden: list[tuple[Summary, float]] = [
            (golden_as_askers(name, r, questions, Mode.HYBRID), _avg_returned(r, questions))
            for name, r in retrievers.items()
        ]
        for name, leaks in scans:
            print(f"{name:<32} leaked chunks: {len(leaks)}")
        header = (
            f"Embedder `{embedder.name}` · {args.size}-token chunks · {len(docs)} docs · "
            f"run {datetime.now(UTC):%Y-%m-%d %H:%M} UTC"
        )
        args.out.write_text(
            render(scans, golden, attacks=len(ATTACKS), users=len(DIRECTORY), header=header),
            encoding="utf-8",
        )
        print(f"Report: {args.out}")
        secure_leaks = scans[0][1]
        return 1 if secure_leaks else 0

    settings = settings or Settings.from_env()
    api = api or make_messages_api(settings)
    retriever = SecureRetriever(
        PgVectorStore(conn, table_name(embedder, args.size), embedder.dim), embedder
    )
    result = ask(api, retriever, args.token, args.question, model=settings.api_model_id)
    print(result.text)
    print("Sources:", ", ".join(dict.fromkeys(h.doc_id for h in result.hits)) or "none")
    return 0
