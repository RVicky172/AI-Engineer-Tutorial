"""Before/after on the golden set: the same first-stage candidates, with and without reranking."""

import statistics
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from ragkit.golden import Question
from ragkit.metrics import QuestionResult, Summary, summarise
from ragkit.retrieval import Mode, Retriever
from rerank.rerankers import Reranker

CANDIDATES = 20
TOP_K = 10  # kept for MRR; recall@5 and evidence@5 read the first 5


@dataclass(frozen=True)
class Comparison:
    first_stage: Mode
    before: list[QuestionResult]  # first stage alone, top 10
    after: list[QuestionResult]  # top 20 from the first stage, reranked, top 10
    rerank_ms: list[float]

    @property
    def p50_ms(self) -> float:
        return statistics.median(self.rerank_ms)

    @property
    def p95_ms(self) -> float:
        return statistics.quantiles(self.rerank_ms, n=20)[-1]

    def summaries(self) -> tuple[Summary, Summary]:
        return (
            summarise(f"{self.first_stage}", self.before),
            summarise(f"{self.first_stage} + rerank", self.after),
        )

    def worse(self) -> list[tuple[QuestionResult, QuestionResult]]:
        """Questions where reranking pushed the first relevant chunk down, lost the answer
        chunk from the top 5, or pushed out one of several relevant documents. These are the
        ones to read (the lab's stretch goal)."""
        out = []
        for b, a in zip(self.before, self.after, strict=True):
            rank_b, rank_a = b.first_relevant_rank or 99, a.first_relevant_rank or 99
            lost_evidence = b.has_evidence(5) and not a.has_evidence(5)
            if rank_a > rank_b or lost_evidence or a.coverage(5) < b.coverage(5):
                out.append((b, a))
        return out


def compare(
    retriever: Retriever,
    reranker: Reranker,
    questions: Sequence[Question],
    first_stage: Mode,
    *,
    clock: Callable[[], float] = time.perf_counter,
) -> Comparison:
    before: list[QuestionResult] = []
    after: list[QuestionResult] = []
    timings: list[float] = []
    for q in questions:
        candidates = retriever.search(q.question, first_stage, CANDIDATES)
        start = clock()
        reranked = reranker.rerank(q.question, candidates, TOP_K)
        timings.append((clock() - start) * 1000)
        for hits, out in ((candidates[:TOP_K], before), (reranked, after)):
            out.append(
                QuestionResult(
                    q.id, frozenset(q.relevant), tuple(hits), 0.0, tuple(q.tags), tuple(q.evidence)
                )
            )
    return Comparison(first_stage, before, after, timings)
