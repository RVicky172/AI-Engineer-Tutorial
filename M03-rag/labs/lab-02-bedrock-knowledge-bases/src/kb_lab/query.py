"""Query the Knowledge Base: Retrieve (chunks only, like our pgvector search) and
RetrieveAndGenerate (retrieval + an answer with citations, fully managed)."""

import time
from collections.abc import Callable, Sequence
from typing import Any

from kb_lab.prepare import doc_id_from_uri
from ragkit.golden import Question
from ragkit.metrics import QuestionResult, Summary, summarise
from ragkit.store import Hit


def group_filter(groups: Sequence[str]) -> dict[str, Any]:
    """Lab 03's rule as a KB metadata filter: the chunk's allowed_groups list must contain at
    least one of the user's groups. orAll needs two or more conditions, so one group is a
    plain listContains."""
    conditions = [{"listContains": {"key": "allowed_groups", "value": g}} for g in sorted(groups)]
    if not conditions:
        raise ValueError("a user with no groups may not search at all")
    return conditions[0] if len(conditions) == 1 else {"orAll": conditions}


def retrieve(
    runtime: Any, kb_id: str, question: str, k: int = 10, *, groups: Sequence[str] | None = None
) -> list[Hit]:
    config: dict[str, Any] = {"numberOfResults": k}
    if groups is not None:
        config["filter"] = group_filter(groups)
    response = runtime.retrieve(
        knowledgeBaseId=kb_id,
        retrievalQuery={"text": question},
        retrievalConfiguration={"vectorSearchConfiguration": config},
    )
    hits = []
    for i, r in enumerate(response["retrievalResults"]):
        uri = r["location"]["s3Location"]["uri"]
        doc_id = r.get("metadata", {}).get("doc_id") or doc_id_from_uri(uri)
        hits.append(Hit(f"{doc_id}#kb{i}", str(doc_id), r["content"]["text"], float(r["score"])))
    return hits


def evaluate(
    runtime: Any,
    kb_id: str,
    questions: Sequence[Question],
    *,
    as_askers: bool = False,
    clock: Callable[[], float] = time.perf_counter,
) -> Summary:
    """The golden set against the KB, scored exactly like the pgvector labs."""
    results = []
    for q in questions:
        start = clock()
        hits = retrieve(runtime, kb_id, q.question, groups=q.groups if as_askers else None)
        results.append(
            QuestionResult(
                q.id,
                frozenset(q.relevant),
                tuple(hits),
                (clock() - start) * 1000,
                tuple(q.tags),
                tuple(q.evidence),
            )
        )
    return summarise("knowledge base" + (" (as askers)" if as_askers else ""), results)


def retrieve_and_generate(
    runtime: Any, kb_id: str, model_arn: str, question: str, *, groups: Sequence[str] | None = None
) -> tuple[str, list[str]]:
    """(answer text, cited doc ids)."""
    vector: dict[str, Any] = {"numberOfResults": 5}
    if groups is not None:
        vector["filter"] = group_filter(groups)
    response = runtime.retrieve_and_generate(
        input={"text": question},
        retrieveAndGenerateConfiguration={
            "type": "KNOWLEDGE_BASE",
            "knowledgeBaseConfiguration": {
                "knowledgeBaseId": kb_id,
                "modelArn": model_arn,
                "retrievalConfiguration": {"vectorSearchConfiguration": vector},
            },
        },
    )
    cited = [
        doc_id_from_uri(ref["location"]["s3Location"]["uri"])
        for citation in response.get("citations", [])
        for ref in citation.get("retrievedReferences", [])
    ]
    return response["output"]["text"], list(dict.fromkeys(cited))
