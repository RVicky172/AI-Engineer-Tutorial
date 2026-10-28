"""Keyword search (BM25) and Reciprocal Rank Fusion.

Vectors capture meaning but blur exact identifiers: `VPN-ERR-812`, `INC0011207`, `AR_DUNNING`.
BM25 matches those exactly. RRF combines two rankings without having to calibrate their scores
against each other: score(d) = sum over rankings of 1 / (k + rank(d))."""

import re
from collections.abc import Sequence

from rank_bm25 import BM25Okapi

from ragkit.store import Hit

# keeps identifiers whole: vpn-err-812, inc0011207, ar_dunning, e-340, 9.1.5
TOKEN = re.compile(r"[a-z0-9]+(?:[-_.][a-z0-9]+)*")


def tokenize(text: str) -> list[str]:
    return TOKEN.findall(text.lower())


class BM25Index:
    def __init__(self, chunks: Sequence[tuple[str, str, str]]) -> None:
        """chunks: (chunk_id, doc_id, text)."""
        if not chunks:
            raise ValueError("BM25 needs at least one chunk")
        self._chunks = list(chunks)
        self._bm25 = BM25Okapi([tokenize(text) for _, _, text in self._chunks])

    def search(self, query: str, k: int = 5, *, allowed: set[str] | None = None) -> list[Hit]:
        """`allowed`: chunk ids the caller may see. Applied before ranking, like the SQL filter."""
        scores = self._bm25.get_scores(tokenize(query))
        ranked = sorted(range(len(self._chunks)), key=lambda i: -float(scores[i]))
        hits = []
        for i in ranked:
            chunk_id, doc_id, text = self._chunks[i]
            if float(scores[i]) <= 0:
                break  # no query term matched: not a result
            if allowed is None or chunk_id in allowed:
                hits.append(Hit(chunk_id, doc_id, text, float(scores[i])))
            if len(hits) == k:
                break
        return hits


def rrf(rankings: Sequence[Sequence[Hit]], k: int = 5, *, c: int = 60) -> list[Hit]:
    """c=60 is the constant from the original RRF paper: it damps the advantage of rank 1, so a
    chunk ranked well by both lists beats one ranked first by only one of them."""
    scores: dict[str, float] = {}
    first_seen: dict[str, Hit] = {}
    for ranking in rankings:
        for rank, hit in enumerate(ranking, 1):
            scores[hit.chunk_id] = scores.get(hit.chunk_id, 0.0) + 1.0 / (c + rank)
            first_seen.setdefault(hit.chunk_id, hit)
    best = sorted(scores, key=lambda cid: -scores[cid])[:k]
    return [Hit(cid, first_seen[cid].doc_id, first_seen[cid].text, scores[cid]) for cid in best]
