from collections import Counter
from collections.abc import Sequence

from rag_acl.evaluate import Leak
from ragkit.metrics import Summary


def _cell(text: str, limit: int = 70) -> str:
    flat = " ".join(text.replace("|", "/").split())
    return flat if len(flat) <= limit else flat[: limit - 3] + "..."


def render(
    scans: Sequence[tuple[str, list[Leak]]],
    golden: Sequence[tuple[Summary, float]],
    *,
    attacks: int,
    users: int,
    header: str,
) -> str:
    """scans: (retriever name, leaks). golden: (summary, avg results returned per question)."""
    lines = [
        "# Lab 03 results: document-level access control",
        "",
        header,
        "",
        f"## Leakage scan: {users} users x {attacks} attack queries x 3 modes, top 10",
        "",
        "A leak is a returned chunk from a document the user may not read, or returned text "
        "containing a marker phrase of such a document.",
        "",
        "| Retriever | Leaked chunks | vector | bm25 | hybrid | Users affected |",
        "|---|---|---|---|---|---|",
    ]
    for name, leaks in scans:
        by_mode = Counter(str(leak.mode) for leak in leaks)
        lines.append(
            f"| {name} | **{len(leaks)}** | {by_mode['vector']} | {by_mode['bm25']} | "
            f"{by_mode['hybrid']} | {len({leak.user for leak in leaks})} |"
        )
    unfiltered = next((leaks for name, leaks in scans if "no access control" in name), [])
    if unfiltered:
        lines += [
            "",
            f"The post-filter output looks clean, but to produce it the application first "
            f"fetched the same {len(unfiltered)} restricted chunks and dropped them in Python. "
            "Anything between the fetch and the drop (a debug log, a cache, an exception "
            "message, a bug) leaks them.",
        ]
    lines += [
        "",
        "## Golden set asked by users holding exactly the question's groups (hybrid, top 5)",
        "",
        "| Retrieval | recall@5 | evidence@5 | MRR | Avg results returned |",
        "|---|---|---|---|---|",
    ]
    lines += [
        f"| {s.name} | {s.recall_at_5:.0%} | {s.evidence_at_5:.0%} | {s.mrr:.2f} | {avg:.1f} |"
        for s, avg in golden
    ]
    for name, leaks in scans:
        if not leaks:
            continue
        lines += [
            "",
            f"## Example leaks: {name}",
            "",
            "| User | Query | Mode | Leaked doc | Why |",
            "|---|---|---|---|---|",
        ]
        seen: set[tuple[str, str]] = set()
        for leak in leaks:
            if (leak.user, leak.doc_id) in seen or len(seen) == 12:
                continue
            seen.add((leak.user, leak.doc_id))
            lines.append(
                f"| {leak.user} | {_cell(leak.query)} | {leak.mode} | {leak.doc_id} | "
                f"{_cell(leak.reason, 50)} |"
            )
    return "\n".join(lines) + "\n"
