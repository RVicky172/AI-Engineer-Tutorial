from collections.abc import Sequence

from rag_pipeline.pipeline import IngestStats
from ragkit.golden import Question
from ragkit.metrics import QuestionResult, Summary

Run = tuple[str, Summary, list[QuestionResult]]  # (config name, summary, per-question results)


def _pct(x: float) -> str:
    return f"{x:.0%}"


def render(
    runs: Sequence[Run],
    ingest: Sequence[IngestStats],
    questions: Sequence[Question],
    *,
    header: str,
) -> str:
    lines = [
        "# Lab 01 results: chunk size and retrieval mode",
        "",
        header,
        "",
        "## Ingestion",
        "",
        "| Chunk size (tokens) | Chunks | Avg tokens | Longer than the model reads | Ingest (s) |",
        "|---|---|---|---|---|",
    ]
    lines += [
        f"| {s.size} | {s.chunks} | {s.avg_tokens:.0f} | {s.over_model_limit} | {s.seconds:.1f} |"
        for s in ingest
    ]
    tags = sorted({t for _, s, _ in runs for t in s.by_tag})
    lines += [
        "",
        "## Retrieval (25 golden questions)",
        "",
        "recall@5: a relevant document is among the top 5 chunks. evidence@5: a top-5 chunk "
        "contains the answer phrase (stricter). coverage@5: share of all relevant documents "
        "found (matters for multi-doc questions). MRR over the top 10.",
        "",
        "| Config | recall@5 | evidence@5 | coverage@5 | MRR | p50 latency (ms) | "
        + " | ".join(f"{t} hits" for t in tags)
        + " |",
        "|---|---|---|---|---|---|" + "---|" * len(tags),
    ]
    for name, s, _ in runs:
        per_tag = " | ".join("{}/{}".format(*s.by_tag.get(t, (0, 0))) for t in tags)
        lines.append(
            f"| {name} | {_pct(s.recall_at_5)} | {_pct(s.evidence_at_5)} | "
            f"{_pct(s.coverage_at_5)} | {s.mrr:.2f} | "
            f"{s.p50_latency_ms:.0f} | {per_tag} |"
        )

    names = [name for name, _, _ in runs]
    by_run = {name: {r.question_id: r for r in results} for name, _, results in runs}
    lines += [
        "",
        "## Rank of the first relevant chunk per question",
        "",
        "`-` means no relevant chunk in the top 10. Rows where any config misses the top 5 are "
        "the ones to read.",
        "",
        "| Question | Tags | " + " | ".join(names) + " |",
        "|---|---|" + "---|" * len(names),
    ]
    for q in questions:
        ranks = [by_run[n][q.id].first_relevant_rank for n in names]
        cells = [str(r) if r is not None else "-" for r in ranks]
        flag = " **" if any(r is None or r > 5 for r in ranks) else ""
        lines.append(f"| {q.id}{flag} | {', '.join(q.tags)} | " + " | ".join(cells) + " |")
    lines += [
        "",
        "## Conclusion",
        "",
        "_Which chunk size and mode would you ship, and why? Which question types does each mode "
        "miss? Read the misses before trusting the averages: 1 question is 4 points here._",
        "",
    ]
    return "\n".join(lines)
