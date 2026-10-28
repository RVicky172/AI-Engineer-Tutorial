"""One chunk table, searchable three ways. Shared by the labs that don't need access control."""

from enum import StrEnum

from ragkit.embedding import Embedder
from ragkit.hybrid import BM25Index, rrf
from ragkit.store import Hit, PgVectorStore

CANDIDATES = 20  # each retriever's list before fusion


class Mode(StrEnum):
    VECTOR = "vector"
    BM25 = "bm25"
    HYBRID = "hybrid"  # vector + BM25 fused with RRF


class Retriever:
    def __init__(self, store: PgVectorStore, embedder: Embedder) -> None:
        self.store, self.embedder = store, embedder
        self._bm25: BM25Index | None = None

    @property
    def bm25(self) -> BM25Index:
        if self._bm25 is None:  # built lazily: vector-only runs never pay for it
            self._bm25 = BM25Index(self.store.all_chunks())
        return self._bm25

    def search(self, question: str, mode: Mode, k: int = 10) -> list[Hit]:
        if mode is Mode.BM25:
            return self.bm25.search(question, k)
        vector_hits = self.store.search(self.embedder.embed_query(question), max(k, CANDIDATES))
        if mode is Mode.VECTOR:
            return vector_hits[:k]
        return rrf([vector_hits, self.bm25.search(question, max(k, CANDIDATES))], k)
