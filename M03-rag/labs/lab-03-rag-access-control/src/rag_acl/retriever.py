"""Retrieval that enforces document permissions, and the anti-patterns it replaces.

The rule: filter BEFORE ranking and limiting, in every retrieval path. Vector search filters in
SQL; BM25 ranks in Python, so it may only score chunk ids the database says the user can read.
Fusion then only ever sees permitted chunks."""

import re
from collections.abc import Sequence
from enum import StrEnum
from typing import Any

import psycopg

from rag_acl.identity import User
from ragkit.chunking import chunk_corpus
from ragkit.corpus import Document
from ragkit.embedding import Embedder
from ragkit.hybrid import BM25Index, rrf
from ragkit.store import Hit, PgVectorStore

CANDIDATES = 20


class Mode(StrEnum):
    VECTOR = "vector"
    BM25 = "bm25"
    HYBRID = "hybrid"


def table_name(embedder: Embedder, size: int) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", embedder.name.lower().rsplit("/", 1)[-1]).strip("_")
    return f"l03_{slug}_{size}"[:63]


def ingest(
    conn: psycopg.Connection[Any], docs: Sequence[Document], embedder: Embedder, *, size: int = 256
) -> PgVectorStore:
    """Chunks inherit `allowed_groups` from their document at ingestion (see PgVectorStore.add):
    permissions must travel with every chunk, because retrieval never looks at documents."""
    chunks = chunk_corpus(
        list(docs), max_tokens=size, overlap_tokens=size // 8, count=embedder.count_tokens
    )
    store = PgVectorStore(conn, table_name(embedder, size), embedder.dim)
    store.reset()
    store.add(chunks, embedder.embed_documents([c.text for c in chunks]), docs)
    store.build_index()
    return store


class SecureRetriever:
    def __init__(self, store: PgVectorStore, embedder: Embedder) -> None:
        self.store, self.embedder = store, embedder
        self._bm25: BM25Index | None = None

    @property
    def bm25(self) -> BM25Index:
        if self._bm25 is None:
            self._bm25 = BM25Index(self.store.all_chunks())
        return self._bm25

    def search(self, user: User, question: str, mode: Mode, k: int = 5) -> list[Hit]:
        """`user` comes from `authenticate()`, never from the question text."""
        return self._search(sorted(user.groups), question, mode, k)

    def _search(self, groups: Sequence[str] | None, question: str, mode: Mode, k: int) -> list[Hit]:
        """groups=None searches everything; only the subclasses below ever pass it."""
        if mode is Mode.VECTOR:
            return self.store.search(self.embedder.embed_query(question), k, groups=groups)
        allowed = None if groups is None else self.store.readable_chunk_ids(groups)
        keyword = self.bm25.search(question, CANDIDATES, allowed=allowed)
        if mode is Mode.BM25:
            return keyword[:k]
        vector = self.store.search(self.embedder.embed_query(question), CANDIDATES, groups=groups)
        return rrf([vector, keyword], k)


class UnfilteredRetriever(SecureRetriever):
    """No access control at all, as in Lab 01. Exists to prove the leakage test can fail."""

    def search(self, user: User, question: str, mode: Mode, k: int = 5) -> list[Hit]:
        return self._search(None, question, mode, k)


class PostFilterRetriever(SecureRetriever):
    """The anti-pattern: take the global top k, then drop what the user may not read.

    It leaks (restricted chunks are fetched into this process, where a log line, a cache or a
    bug can expose them) and it loses recall (if 4 of the top 5 are restricted, the user gets 1
    result, though permitted relevant chunks were ranked 6th to 9th)."""

    def search(self, user: User, question: str, mode: Mode, k: int = 5) -> list[Hit]:
        top_k = self._search(None, question, mode, k)
        readable = self.store.readable_chunk_ids(sorted(user.groups))
        return [h for h in top_k if h.chunk_id in readable]
