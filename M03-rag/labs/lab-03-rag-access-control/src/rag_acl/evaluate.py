from collections.abc import Sequence
from dataclasses import dataclass

from rag_acl.attacks import ATTACKS, MARKERS
from rag_acl.identity import DIRECTORY, User
from rag_acl.retriever import Mode, SecureRetriever
from ragkit.corpus import Document
from ragkit.golden import Question
from ragkit.metrics import QuestionResult, normalize, summarise
from ragkit.metrics import Summary as RetrievalSummary
from ragkit.store import Hit


@dataclass(frozen=True)
class Leak:
    user: str
    query: str
    mode: Mode
    doc_id: str
    reason: str  # "unreadable doc" or "marker: <phrase>"


def readable_docs(user: User, docs: Sequence[Document]) -> set[str]:
    return {d.doc_id for d in docs if user.groups & set(d.allowed_groups)}


def leaks_in(
    user: User, query: str, mode: Mode, hits: Sequence[Hit], docs: Sequence[Document]
) -> list[Leak]:
    allowed = readable_docs(user, docs)
    found = [
        Leak(user.user_id, query, mode, h.doc_id, "unreadable doc")
        for h in hits
        if h.doc_id not in allowed
    ]
    for doc_id, marker in MARKERS.items():
        if doc_id in allowed:
            continue
        found += [
            Leak(user.user_id, query, mode, h.doc_id, f"marker: {marker}")
            for h in hits
            if normalize(marker) in normalize(h.text)  # '**Project Kestrel**' still matches
        ]
    return found


def leak_scan(
    retriever: SecureRetriever,
    docs: Sequence[Document],
    users: Sequence[User] = tuple(DIRECTORY.values()),
    queries: Sequence[str] = ATTACKS,
    modes: Sequence[Mode] = tuple(Mode),
    k: int = 10,
) -> list[Leak]:
    """Every user x every attack x every mode. A secure retriever returns []."""
    return [
        leak
        for user in users
        for query in queries
        for mode in modes
        for leak in leaks_in(user, query, mode, retriever.search(user, query, mode, k), docs)
    ]


def golden_as_askers(
    name: str, retriever: SecureRetriever, questions: Sequence[Question], mode: Mode
) -> RetrievalSummary:
    """Each golden question asked by a user holding exactly its `groups`. Access control must
    not cost recall: every relevant doc is readable by those groups."""
    results = []
    for q in questions:
        user = User(f"asker-{q.id}", frozenset(q.groups))
        hits = retriever.search(user, q.question, mode, 10)
        results.append(
            QuestionResult(
                q.id, frozenset(q.relevant), tuple(hits), 0.0, tuple(q.tags), tuple(q.evidence)
            )
        )
    return summarise(name, results)
