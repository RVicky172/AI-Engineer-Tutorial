import json
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any

import boto3
import psycopg
import pytest
from botocore.stub import Stubber
from llm_common import Settings
from llm_common.fake import FakeMessages, make_message, real_sdk_messages

from ragkit.corpus import Document, load_corpus
from ragkit.embedding import Embedder, HashEmbedder
from ragkit.golden import Question, load_golden
from ragkit.retrieval import Mode, Retriever
from ragkit.store import Hit, build_table, connect
from rerank.cli import LABS, main, table_name
from rerank.experiment import compare
from rerank.judge import GRADE_SCHEMA, build_request, judge
from rerank.rerankers import (
    BedrockReranker,
    CrossEncoderReranker,
    LexicalReranker,
    Reranker,
    make_reranker,
)

EMB = HashEmbedder(dim=256)
HITS = [
    Hit("a#0", "a", "printer toner is low", 0.9),
    Hit("b#0", "b", "reset your SSO password at the reset page", 0.8),
    Hit("c#0", "c", "VPN gateway failover", 0.7),
]
ARN = "arn:aws:bedrock:us-west-2::foundation-model/amazon.rerank-v1:0"


@pytest.fixture(scope="session")
def conn() -> Iterator[psycopg.Connection[Any]]:
    try:
        connection = connect()
    except psycopg.OperationalError as exc:
        pytest.skip(f"pgvector not reachable ({exc}); run `docker compose up -d` in labs/")
    yield connection
    connection.close()


@pytest.fixture(scope="session")
def docs() -> list[Document]:
    return load_corpus(LABS / "corpus")


@pytest.fixture(scope="session")
def questions(docs: list[Document]) -> list[Question]:
    return load_golden(LABS / "golden.yaml", {d.doc_id for d in docs})


@pytest.fixture(scope="session")
def retriever(conn: psycopg.Connection[Any], docs: list[Document]) -> Retriever:
    return Retriever(build_table(conn, docs, EMB, table=table_name(EMB, 256), size=256), EMB)


def test_lexical_reranker_orders_by_overlap_and_keeps_ties_stable() -> None:
    out = LexicalReranker().rerank("how do I reset my password", HITS, 2)
    assert [h.doc_id for h in out] == ["b", "a"]  # b matches; a and c tie at 0, a came first
    assert out[0].score == 2.0  # "reset", "password"


def test_bedrock_reranker_sends_a_request_the_real_api_model_accepts() -> None:
    """Stubber validates our parameters against botocore's model of the Rerank API, so a
    wrong field name fails here instead of on the first billed call."""
    client = boto3.client(
        "bedrock-agent-runtime",
        region_name="us-west-2",
        aws_access_key_id="test",
        aws_secret_access_key="test",  # noqa: S106 (stub, no calls)
    )
    reranker = BedrockReranker(ARN, client)
    expected = {
        "queries": [{"type": "TEXT", "textQuery": {"text": "reset password"}}],
        "sources": [
            {
                "type": "INLINE",
                "inlineDocumentSource": {"type": "TEXT", "textDocument": {"text": h.text}},
            }
            for h in HITS
        ],
        "rerankingConfiguration": {
            "type": "BEDROCK_RERANKING_MODEL",
            "bedrockRerankingConfiguration": {
                "numberOfResults": 2,
                "modelConfiguration": {"modelArn": ARN},
            },
        },
    }
    response = {
        "results": [{"index": 1, "relevanceScore": 0.93}, {"index": 2, "relevanceScore": 0.1}]
    }
    with Stubber(client) as stub:
        stub.add_response("rerank", response, expected)
        out = reranker.rerank("reset password", HITS, 2)
        stub.assert_no_pending_responses()
    assert [(h.doc_id, h.score) for h in out] == [("b", 0.93), ("c", 0.1)]
    assert reranker.name == "amazon.rerank-v1:0"
    assert reranker.rerank("q", [], 5) == []


@pytest.mark.model
def test_cross_encoder_prefers_the_relevant_passage() -> None:
    reranker = CrossEncoderReranker()
    out = reranker.rerank("How do I reset my password?", HITS, 3)
    assert out[0].doc_id == "b"
    assert reranker.rerank("q", [], 3) == []


def test_make_reranker() -> None:
    assert isinstance(make_reranker("lexical"), LexicalReranker)
    with pytest.raises(ValueError, match="unknown reranker"):
        make_reranker("colbert")


def test_compare_measures_the_same_candidates_before_and_after(
    retriever: Retriever, questions: list[Question]
) -> None:
    ticks = iter(float(i) / 1000 for i in range(100))
    c = compare(retriever, LexicalReranker(), questions[:6], Mode.HYBRID, clock=lambda: next(ticks))
    assert len(c.before) == len(c.after) == len(c.rerank_ms) == 6
    assert c.rerank_ms == pytest.approx([1.0] * 6)
    assert c.p50_ms == pytest.approx(1.0) and c.p95_ms == pytest.approx(1.0)
    for b, a in zip(c.before, c.after, strict=True):
        # reranking may only reorder (and drop) candidates, never invent new chunks
        assert {h.chunk_id for h in a.hits} <= {
            h.chunk_id
            for h in retriever.search(
                next(q.question for q in questions if q.id == b.question_id), Mode.HYBRID, 20
            )
        }
    before, after = c.summaries()
    assert (before.name, after.name) == ("hybrid", "hybrid + rerank")


def test_worse_flags_rank_drops_lost_evidence_and_lost_coverage(
    retriever: Retriever, questions: list[Question]
) -> None:
    class Reverse:
        name = "reverse"

        def rerank(self, query: str, hits: Sequence[Hit], k: int) -> list[Hit]:
            return list(reversed(hits))[:k]

    c = compare(retriever, Reverse(), questions, Mode.HYBRID)
    assert len(c.worse()) >= len(questions) // 2  # reversing a good ranking hurts most questions


def test_judge_request_and_parsing() -> None:
    req = build_request("Q?", "ref", "cand", model="m")
    assert req["output_config"]["format"] == {"type": "json_schema", "schema": GRADE_SCHEMA}
    assert "<candidate>cand</candidate>" in req["messages"][0]["content"]
    api, sent = real_sdk_messages(make_message('{"reason": "ok", "score": 4}'))
    grade = judge(api, "Q?", "ref", "cand", model="m")
    assert (grade.score, grade.reason) == (4, "ok")
    assert sent[0]["output_config"]["format"]["schema"]["properties"]["score"]["enum"] == [
        1,
        2,
        3,
        4,
        5,
    ]

    refused = judge(FakeMessages([make_message(stop_reason="refusal")]), "Q", "r", "c", model="m")
    assert refused.score == 0


def hash_factory(_: str) -> Embedder:
    return EMB


def lexical_factory(kind: str, **_: Any) -> Reranker:
    return LexicalReranker()


def test_cli_run_and_answers(conn: psycopg.Connection[Any], tmp_path: Path) -> None:
    out = tmp_path / "results.md"
    code = main(
        ["--embedder", "hash", "--reranker", "lexical", "run", "--out", str(out)],
        conn=conn,
        embedder_factory=hash_factory,
        reranker_factory=lexical_factory,
    )
    report = out.read_text(encoding="utf-8")
    assert code == 0
    assert "| **hybrid + rerank** |" in report and "## Where reranking made vector worse" in report

    def model(request: dict[str, Any]) -> Any:
        if "format" in request["output_config"]:  # the judge
            return make_message(json.dumps({"reason": "fine", "score": 4}))
        return make_message("Answer [kb-printer-error-codes].")

    api = FakeMessages(model)
    answers = tmp_path / "answers.md"
    code = main(
        [
            "--embedder",
            "hash",
            "--reranker",
            "bedrock",
            "--bedrock-model-arn",
            ARN,
            "answers",
            "--limit",
            "2",
            "--out",
            str(answers),
        ],
        conn=conn,
        embedder_factory=hash_factory,
        reranker_factory=lexical_factory,
        api=api,
        settings=Settings(model="m"),
    )
    text = answers.read_text(encoding="utf-8")
    assert code == 0 and len(api.calls) == 8  # 2 questions x (answer + judge) x before/after
    assert "**Mean score: before 4.00 -> after 4.00**" in text
