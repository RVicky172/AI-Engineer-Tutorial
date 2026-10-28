"""Ingest the corpus at several chunk sizes, retrieve three ways, and score against the golden
set. Retrieval is evaluated on its own, with no model call, so its numbers are free and exact."""

import re
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

import psycopg

from ragkit.chunking import Chunk, chunk_corpus
from ragkit.corpus import Document
from ragkit.embedding import Embedder
from ragkit.golden import Question
from ragkit.hybrid import BM25Index, rrf
from ragkit.metrics import QuestionResult
from ragkit.store import Hit, PgVectorStore

CANDIDATES = 20  # each retriever's list before fusion
TOP_K = 10  # kept per question: recall@5 reads the first 5, MRR all 10


class Mode(StrEnum):
    VECTOR = "vector"
    BM25 = "bm25"
    HYBRID = "hybrid"  # vector + BM25 fused with RRF


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


class Retriever:
    """One chunk table, searchable three ways."""

    def __init__(self, store: PgVectorStore, embedder: Embedder) -> None:
        self.store, self.embedder = store, embedder
        self._bm25: BM25Index | None = None

    @property
    def bm25(self) -> BM25Index:
        if self._bm25 is None:  # built lazily: vector-only runs never pay for it
            self._bm25 = BM25Index(self.store.all_chunks())
        return self._bm25

    def search(self, question: str, mode: Mode, k: int = TOP_K) -> list[Hit]:
        if mode is Mode.BM25:
            return self.bm25.search(question, k)
        vector_hits = self.store.search(self.embedder.embed_query(question), CANDIDATES)
        if mode is Mode.VECTOR:
            return vector_hits[:k]
        return rrf([vector_hits, self.bm25.search(question, CANDIDATES)], k)


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
