"""LLM-as-judge: score an answer 1-5 against the golden reference answer.

The judge sees the question, the reference and the candidate answer, never which pipeline
produced it, so it can't favour "the reranked one". Structured output guarantees a parseable
grade. Judges are models too: spot-check a sample of grades by hand before trusting them."""

import json
from dataclasses import dataclass
from typing import Any

from llm_common import MessagesAPI, text_of

JUDGE_SYSTEM = """\
You grade answers given by an IT help assistant. Compare the candidate answer with the \
reference answer for the same question.

Score:
5: correct and complete; every key fact of the reference is present, nothing wrong.
4: correct, but misses a minor detail.
3: partly correct; misses a key fact, or adds an unsupported claim.
2: mostly wrong or mostly missing, with some relevant content.
1: wrong, irrelevant, or a refusal when the reference has an answer.

Judge facts, not wording or length. The candidate's citations in [brackets] do not matter here."""

GRADE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "reason": {"type": "string", "description": "One sentence: what matches or is missing"},
        "score": {"type": "integer", "enum": [1, 2, 3, 4, 5]},
    },
    "required": ["reason", "score"],
    "additionalProperties": False,
}


@dataclass(frozen=True)
class Grade:
    score: int  # 0 = the judge's reply was unusable
    reason: str


def build_request(question: str, reference: str, candidate: str, *, model: str) -> dict[str, Any]:
    return {
        "model": model,
        "max_tokens": 2048,
        "system": [{"type": "text", "text": JUDGE_SYSTEM, "cache_control": {"type": "ephemeral"}}],
        "messages": [
            {
                "role": "user",
                "content": f"<question>{question}</question>\n<reference>{reference}</reference>\n"
                f"<candidate>{candidate}</candidate>",
            }
        ],
        # reason before score: the model commits to an explanation, then the number
        "output_config": {
            "effort": "low",
            "format": {"type": "json_schema", "schema": GRADE_SCHEMA},
        },
    }


def judge(api: MessagesAPI, question: str, reference: str, candidate: str, *, model: str) -> Grade:
    reply = api.create(**build_request(question, reference, candidate, model=model))
    if reply.stop_reason in ("refusal", "max_tokens"):
        return Grade(0, f"judge stopped: {reply.stop_reason}")
    data = json.loads(text_of(reply))
    return Grade(int(data["score"]), str(data["reason"]))
