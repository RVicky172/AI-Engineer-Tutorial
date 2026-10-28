import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import psycopg
import pytest
from llm_common import Settings
from llm_common.fake import FakeMessages, make_message

from rag_pipeline.cli import LABS, main
from rag_pipeline.pipeline import evaluate, ingest, table_name
from ragkit.corpus import Document, load_corpus
from ragkit.embedding import Embedder, HashEmbedder
from ragkit.golden import Question, load_golden
from ragkit.retrieval import Mode, Retriever
from ragkit.store import PgVectorStore, connect

EMB = HashEmbedder(dim=128)  # deterministic and lexical: tests never download a model


@pytest.fixture(scope="session")
def conn() -> Iterator[psycopg.Connection[Any]]:
    try:
        connection = connect()
    except psycopg.OperationalError as exc:
        pytest.skip(f"pgvector not reachable ({exc}); run `docker compose up -d` in labs/")
    yield connection
    connection.close()


@pytest.fixture(scope="session")
def docs() -> list[Document]:
    return load_corpus(LABS / "corpus")


@pytest.fixture(scope="session")
def questions(docs: list[Document]) -> list[Question]:
    return load_golden(LABS / "golden.yaml", {d.doc_id for d in docs})


@pytest.fixture(scope="session")
def retriever(conn: psycopg.Connection[Any], docs: list[Document]) -> Retriever:
    ingest(conn, docs, EMB, size=256)
    return Retriever(PgVectorStore(conn, table_name(EMB, 256), EMB.dim), EMB)


def hash_factory(_: str) -> Embedder:
    return EMB


def test_table_names_are_valid_identifiers() -> None:
    assert table_name(EMB, 256) == "l01_hash_bow_256"

    class Named(HashEmbedder):
        name = "BAAI/bge-small-en-v1.5"

    assert table_name(Named(), 128) == "l01_bge_small_en_v1_5_128"


def test_ingest_reports_what_it_stored(conn: psycopg.Connection[Any], docs: list[Document]) -> None:
    ticks = iter([0.0, 2.5])
    stats = ingest(conn, docs, EMB, size=128, overlap=0.1, clock=lambda: next(ticks))
    assert stats.table == "l01_hash_bow_128"
    assert stats.chunks == PgVectorStore(conn, stats.table, EMB.dim).count() > len(docs)
    assert stats.avg_tokens <= 128 and stats.over_model_limit == 0
    assert stats.seconds == 2.5


@pytest.mark.parametrize("mode", list(Mode))
def test_every_mode_returns_ranked_chunks(retriever: Retriever, mode: Mode) -> None:
    hits = retriever.search("What does printer error E-340 mean?", mode, k=5)
    assert 0 < len(hits) <= 5
    assert hits[0].doc_id == "kb-printer-error-codes"


def test_bm25_finds_exact_identifiers(
    retriever: Retriever,
) -> None:
    hits = retriever.search("AR_DUNNING", Mode.BM25, k=3)
    assert hits[0].doc_id == "rb-erp-batch-job-rerun"


def test_evaluate_scores_every_golden_question(
    retriever: Retriever, questions: list[Question]
) -> None:
    results = evaluate(retriever, questions[:5], Mode.HYBRID)
    assert [r.question_id for r in results] == ["q01", "q02", "q03", "q04", "q05"]
    assert all(len(r.hits) <= 10 and r.evidence for r in results)
    assert sum(r.hit(5) for r in results) >= 3  # even a bag-of-words embedder finds most


def test_cli_run_writes_the_report(conn: psycopg.Connection[Any], tmp_path: Path) -> None:
    out = tmp_path / "results.md"
    code = main(
        [
            "--embedder",
            "hash",
            "run",
            "--sizes",
            "128,256",
            "--modes",
            "vector,hybrid",
            "--out",
            str(out),
        ],
        conn=conn,
        embedder_factory=hash_factory,
    )
    report = out.read_text(encoding="utf-8")
    assert code == 0
    assert "| 128 | " in report and "| 256 hybrid | " in report
    assert re.search(r"\| q01(?: \*\*)? \| keyword \| ", report)

    again = main(
        ["run", "--sizes", "256", "--modes", "bm25", "--skip-ingest", "--out", str(out)],
        conn=conn,
        embedder_factory=hash_factory,
    )
    assert again == 0 and "## Ingestion" in out.read_text(encoding="utf-8")


def test_cli_ask_prints_answer_and_checks_citations(
    conn: psycopg.Connection[Any], retriever: Retriever, capsys: pytest.CaptureFixture[str]
) -> None:
    def reply_citing(doc_id: str) -> FakeMessages:
        return FakeMessages([make_message(f"Switch it off for 10 minutes [{doc_id}].")])

    args = ["ask", "What does printer error E-340 mean?", "--size", "256"]
    ok = main(
        args,
        conn=conn,
        embedder_factory=hash_factory,
        api=reply_citing("kb-printer-error-codes"),
        settings=Settings(model="m"),
    )
    assert ok == 0
    assert "Citations ok: True" in capsys.readouterr().out

    bad = main(
        args,
        conn=conn,
        embedder_factory=hash_factory,
        api=reply_citing("made-up-doc"),
        settings=Settings(model="m"),
    )
    assert bad == 1
    assert "not in context: ['made-up-doc']" in capsys.readouterr().out


def test_cli_answer_golden_writes_cited_answers(
    conn: psycopg.Connection[Any], retriever: Retriever, tmp_path: Path
) -> None:
    out = tmp_path / "answers.md"
    api = FakeMessages(lambda req: make_message("See [kb-printer-error-codes]."))
    code = main(
        ["answer-golden", "--limit", "2", "--out", str(out)],
        conn=conn,
        embedder_factory=hash_factory,
        api=api,
        settings=Settings(model="m"),
    )
    text = out.read_text(encoding="utf-8")
    assert code == 0 and len(api.calls) == 2
    assert "## q01:" in text and "- Reference:" in text
    assert "**Citations valid:" in text
