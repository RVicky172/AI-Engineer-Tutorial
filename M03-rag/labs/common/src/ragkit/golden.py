from collections.abc import Sequence
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from ragkit.corpus import Document
from ragkit.metrics import normalize


class Question(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    question: str
    relevant: list[str] = Field(min_length=1)
    evidence: list[str] = Field(min_length=1)
    answer: str
    groups: list[str] = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)


class GoldenSet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    questions: list[Question]


def load_golden(path: Path, known_doc_ids: set[str] | None = None) -> list[Question]:
    """Pass the corpus doc ids to catch a label pointing at a renamed or missing document:
    such a question can never be answered and silently lowers recall."""
    questions = GoldenSet.model_validate(yaml.safe_load(path.read_text(encoding="utf-8"))).questions
    ids = [q.id for q in questions]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate question ids")
    if known_doc_ids is not None:
        unknown = sorted({d for q in questions for d in q.relevant} - known_doc_ids)
        if unknown:
            raise ValueError(f"golden set refers to unknown documents: {unknown}")
    return questions


def check_evidence(questions: Sequence[Question], docs: Sequence[Document]) -> None:
    """Every evidence phrase must occur in one of the question's relevant documents. A phrase
    that matches nothing makes evidence@k silently zero for that question."""
    text = {d.doc_id: normalize(d.text) for d in docs}
    for q in questions:
        for phrase in q.evidence:
            if not any(normalize(phrase) in text.get(doc_id, "") for doc_id in q.relevant):
                raise ValueError(f"{q.id}: evidence {phrase!r} is in none of {q.relevant}")
