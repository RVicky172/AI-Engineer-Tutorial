"""Retrieval metrics on the golden set. Retrieval is judged at the *document* level: a question
is answered if a chunk of a relevant document reaches the model."""

import re
import statistics
from collections.abc import Sequence
from dataclasses import dataclass

from ragkit.store import Hit


def normalize(text: str) -> str:
    """Case, whitespace and markdown emphasis don't matter when looking for an answer phrase."""
    return re.sub(r"\s+", " ", text.replace("*", "").replace("`", "")).strip().lower()


def doc_ranking(hits: Sequence[Hit]) -> list[str]:
    """Documents in order of their best chunk. Three chunks of one doc are still one doc."""
    return list(dict.fromkeys(h.doc_id for h in hits))


def hit_at_k(hits: Sequence[Hit], relevant: set[str], k: int) -> bool:
    """recall@k as the course defines it: does ANY relevant doc appear in the top k chunks?"""
    return bool(relevant & {h.doc_id for h in hits[:k]})


def coverage_at_k(hits: Sequence[Hit], relevant: set[str], k: int) -> float:
    """Share of the relevant docs found in the top k chunks. Matters for multi-doc questions,
    where finding one of two documents gives half an answer."""
    return len(relevant & {h.doc_id for h in hits[:k]}) / len(relevant)


def evidence_at_k(hits: Sequence[Hit], evidence: Sequence[str], k: int) -> bool:
    """Does a top-k CHUNK contain an answer phrase? Stricter than recall@k: the right document
    can be retrieved through a chunk that doesn't hold the answer."""
    chunks = [normalize(h.text) for h in hits[:k]]
    return any(normalize(e) in c for e in evidence for c in chunks)


def reciprocal_rank(hits: Sequence[Hit], relevant: set[str]) -> float:
    """1 / rank of the first chunk from a relevant doc; 0 if none was retrieved."""
    for rank, hit in enumerate(hits, 1):
        if hit.doc_id in relevant:
            return 1.0 / rank
    return 0.0


@dataclass(frozen=True)
class QuestionResult:
    question_id: str
    relevant: frozenset[str]
    hits: tuple[Hit, ...]
    latency_ms: float
    tags: tuple[str, ...] = ()
    evidence: tuple[str, ...] = ()

    def hit(self, k: int) -> bool:
        return hit_at_k(self.hits, set(self.relevant), k)

    def has_evidence(self, k: int) -> bool:
        return evidence_at_k(self.hits, self.evidence, k)

    def coverage(self, k: int) -> float:
        return coverage_at_k(self.hits, set(self.relevant), k)

    @property
    def rr(self) -> float:
        return reciprocal_rank(self.hits, set(self.relevant))

    @property
    def first_relevant_rank(self) -> int | None:
        rr = self.rr
        return round(1 / rr) if rr else None


@dataclass(frozen=True)
class Summary:
    name: str
    n: int
    recall_at_5: float
    evidence_at_5: float
    coverage_at_5: float
    mrr: float
    p50_latency_ms: float
    by_tag: dict[str, tuple[int, int]]  # tag -> (hits@5, questions)


def summarise(name: str, results: Sequence[QuestionResult], k: int = 5) -> Summary:
    tags = sorted({t for r in results for t in r.tags})
    return Summary(
        name=name,
        n=len(results),
        recall_at_5=sum(r.hit(k) for r in results) / len(results),
        evidence_at_5=sum(r.has_evidence(k) for r in results) / len(results),
        coverage_at_5=statistics.fmean(r.coverage(k) for r in results),
        mrr=statistics.fmean(r.rr for r in results),
        p50_latency_ms=statistics.median(r.latency_ms for r in results),
        by_tag={
            t: (sum(r.hit(k) for r in results if t in r.tags), sum(t in r.tags for r in results))
            for t in tags
        },
    )
