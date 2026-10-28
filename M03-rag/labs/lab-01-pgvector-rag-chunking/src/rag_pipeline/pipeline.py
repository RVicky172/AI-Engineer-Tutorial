"""Ingest the corpus at several chunk sizes, retrieve three ways, and score against the golden
set. Retrieval is evaluated on its own, with no model call, so its numbers are free and exact."""

import re
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

import psycopg

from ragkit.chunking import Chunk, chunk_corpus
from ragkit.corpus import Document
from ragkit.embedding import Embedder
from ragkit.golden import Question
from ragkit.metrics import QuestionResult
from ragkit.retrieval import Mode, Retriever
from ragkit.store import PgVectorStore

TOP_K = 10  # kept per question: recall@5 reads the first 5, MRR all 10


def table_name(embedder: Embedder, size: int) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", embedder.name.lower().rsplit("/", 1)[-1]).strip("_")
    return f"l01_{slug}_{size}"[:63]


@dataclass(frozen=True)
class IngestStats:
    size: int
    table: str
    chunks: int
    avg_tokens: float
    over_model_limit: int  # chunks longer than the embedder reads: their tail is ignored
    seconds: float


def ingest(
    conn: psycopg.Connection[Any],
    docs: Sequence[Document],
    embedder: Embedder,
    *,
    size: int,
    overlap: float = 0.125,
    clock: Callable[[], float] = time.perf_counter,
) -> IngestStats:
    start = clock()
    chunks: list[Chunk] = chunk_corpus(
        list(docs), max_tokens=size, overlap_tokens=int(size * overlap), count=embedder.count_tokens
    )
    vectors = embedder.embed_documents([c.text for c in chunks])
    store = PgVectorStore(conn, table_name(embedder, size), embedder.dim)
    store.reset()
    store.add(chunks, vectors, docs)
    store.build_index()
    return IngestStats(
        size=size,
        table=store.name,
        chunks=len(chunks),
        avg_tokens=sum(c.tokens for c in chunks) / len(chunks),
        over_model_limit=sum(c.tokens > embedder.max_tokens for c in chunks),
        seconds=clock() - start,
    )


def evaluate(
    retriever: Retriever,
    questions: Sequence[Question],
    mode: Mode,
    *,
    clock: Callable[[], float] = time.perf_counter,
) -> list[QuestionResult]:
    results = []
    for q in questions:
        start = clock()
        hits = retriever.search(q.question, mode)
        results.append(
            QuestionResult(
                question_id=q.id,
                relevant=frozenset(q.relevant),
                hits=tuple(hits),
                latency_ms=(clock() - start) * 1000,
                tags=tuple(q.tags),
                evidence=tuple(q.evidence),
            )
        )
    return results
