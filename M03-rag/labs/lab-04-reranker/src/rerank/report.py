from collections.abc import Sequence

from ragkit.golden import Question
from rerank.experiment import Comparison


def _rank(r: int | None) -> str:
    return "-" if r is None else str(r)


def render(comparisons: Sequence[Comparison], questions: Sequence[Question], *, header: str) -> str:
    lines = [
        "# Lab 04 results: reranking the top 20 down to 5",
        "",
        header,
        "",
        "## Retrieval before and after",
        "",
        "| Config | recall@5 | evidence@5 | coverage@5 | MRR | Rerank p50 (ms) | Rerank p95 (ms) |",
        "|---|---|---|---|---|---|---|",
    ]
    for c in comparisons:
        before, after = c.summaries()
        lines += [
            f"| {before.name} | {before.recall_at_5:.0%} | {before.evidence_at_5:.0%} | "
            f"{before.coverage_at_5:.0%} | {before.mrr:.2f} | - | - |",
            f"| **{after.name}** | {after.recall_at_5:.0%} | {after.evidence_at_5:.0%} | "
            f"{after.coverage_at_5:.0%} | {after.mrr:.2f} | {c.p50_ms:.0f} | {c.p95_ms:.0f} |",
        ]
    names = [str(c.first_stage) for c in comparisons]
    lines += [
        "",
        "## Rank of the first relevant chunk: before -> after",
        "",
        "| Question | Tags | " + " | ".join(names) + " |",
        "|---|---|" + "---|" * len(names),
    ]
    for i, q in enumerate(questions):
        cells = []
        for c in comparisons:
            b, a = c.before[i].first_relevant_rank, c.after[i].first_relevant_rank
            mark = " (worse)" if (a or 99) > (b or 99) else ""
            cells.append(f"{_rank(b)} -> {_rank(a)}{mark}")
        lines.append(f"| {q.id} | {', '.join(q.tags)} | " + " | ".join(cells) + " |")

    by_id = {q.id: q for q in questions}
    for c in comparisons:
        worse = c.worse()
        lines += ["", f"## Where reranking made {c.first_stage} worse ({len(worse)})", ""]
        if not worse:
            lines.append("None.")
        for was, now in worse:
            lines += [
                f"**{was.question_id}**: {by_id[was.question_id].question}  ",
                f"relevant: {', '.join(sorted(was.relevant))} · coverage@5 "
                f"{was.coverage(5):.0%} -> {now.coverage(5):.0%}  ",
                f"before: {', '.join(h.doc_id for h in was.hits[:3])}  ",
                f"after: {', '.join(h.doc_id for h in now.hits[:3])}",
                "",
            ]
    lines += [
        "## Conclusion",
        "",
        "_Is the quality gain worth the added latency? For each 'worse' question, say why the "
        "cross-encoder preferred the wrong chunk (it was trained on web search, not runbooks)._",
        "",
    ]
    return "\n".join(lines)
