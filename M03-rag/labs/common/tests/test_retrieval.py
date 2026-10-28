import io
import json
from typing import Any

import numpy as np
import psycopg
import pytest

from ragkit.chunking import Chunk, chunk_corpus
from ragkit.corpus import Document
from ragkit.embedding import HashEmbedder, LocalEmbedder, TitanEmbedder, make_embedder
from ragkit.hybrid import BM25Index, rrf, tokenize
from ragkit.metrics import (
    QuestionResult,
    coverage_at_k,
    doc_ranking,
    evidence_at_k,
    hit_at_k,
    normalize,
    reciprocal_rank,
    summarise,
)
from ragkit.store import Hit, PgVectorStore
from tests.conftest import make_doc


def hit(doc_id: str, text: str = "", n: int = 0) -> Hit:
    return Hit(f"{doc_id}#{n}", doc_id, text, 1.0)


def test_metrics_on_a_hand_made_ranking() -> None:
    hits = [hit("a", "nothing"), hit("b", "The **Answer** is here", 0), hit("b", "x", 1), hit("c")]
    assert doc_ranking(hits) == ["a", "b", "c"]
    assert hit_at_k(hits, {"b"}, 2) and not hit_at_k(hits, {"c"}, 2)
    assert coverage_at_k(hits, {"b", "z"}, 5) == 0.5
    assert evidence_at_k(hits, ["answer is   HERE"], 2)
    assert not evidence_at_k(hits, ["answer is here"], 1)
    assert reciprocal_rank(hits, {"c"}) == 0.25
    assert reciprocal_rank(hits, {"z"}) == 0.0
    assert normalize("`A`  *b*\n") == "a b"


def test_summary_counts_tags_and_first_relevant_rank() -> None:
    found = QuestionResult("q1", frozenset({"b"}), (hit("a"), hit("b")), 10, ("kw",), ("x",))
    missed = QuestionResult("q2", frozenset({"z"}), (hit("a"),), 30, ("kw",))
    assert found.first_relevant_rank == 2 and missed.first_relevant_rank is None
    s = summarise("cfg", [found, missed])
    assert (s.recall_at_5, s.evidence_at_5, s.mrr, s.p50_latency_ms) == (0.5, 0.0, 0.25, 20)
    assert s.by_tag == {"kw": (1, 2)}


def test_tokenizer_keeps_identifiers_whole() -> None:
    assert tokenize("Error VPN-ERR-812 on INC0011207, run AR_DUNNING v9.1.5") == [
        "error",
        "vpn-err-812",
        "on",
        "inc0011207",
        "run",
        "ar_dunning",
        "v9.1.5",
    ]


def test_bm25_finds_exact_identifiers_and_respects_the_allowed_set() -> None:
    index = BM25Index(
        [
            ("a#0", "a", "printer error E-340 fuser"),
            ("b#0", "b", "printer jams"),
            ("c#0", "c", "vpn"),
        ]
    )
    assert [h.doc_id for h in index.search("what is E-340?")] == ["a"]
    assert index.search("E-340", allowed={"b#0"}) == []
    assert [h.doc_id for h in index.search("printer", k=1)] in (["a"], ["b"])
    with pytest.raises(ValueError):
        BM25Index([])


def test_rrf_rewards_agreement_between_rankings() -> None:
    vector = [hit("a"), hit("b"), hit("c")]
    keyword = [hit("d"), hit("b"), hit("c")]
    fused = rrf([vector, keyword], k=2)
    # b (2nd in both) and c (3rd in both) beat a and d (1st in only one list)
    assert [h.doc_id for h in fused] == ["b", "c"]
    assert fused[0].score == pytest.approx(2 / 62)


def test_hash_embedder_is_deterministic_and_lexical() -> None:
    e = make_embedder("hash", dim=128)
    a, b, c = e.embed_documents(["vpn gateway down", "the vpn gateway", "printer toner"])
    assert np.allclose(e.embed_query("vpn gateway down"), a)
    assert float(a @ b) > float(a @ c)
    assert float(np.linalg.norm(a)) == pytest.approx(1.0)
    assert e.count_tokens("a b c") == 3
    assert not e.embed_query("").any()  # no words: zero vector, no division by zero


class FakeBedrock:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def invoke_model(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        return {"body": io.BytesIO(json.dumps({"embedding": [0.6, 0.8]}).encode())}


def test_titan_sends_one_request_per_text_with_the_right_body() -> None:
    client = FakeBedrock()
    e = TitanEmbedder(client, dim=256)
    vectors = e.embed_documents(["a", "b"])
    assert vectors.shape == (2, 2) and np.allclose(e.embed_query("q"), [0.6, 0.8])
    body = json.loads(client.calls[0]["body"])
    assert body == {"inputText": "a", "dimensions": 256, "normalize": True}
    assert client.calls[0]["modelId"] == "amazon.titan-embed-text-v2:0"
    assert e.count_tokens("ERP-4012 timed out.") == 6  # ERP - 4012 timed out .


def test_unknown_embedder_kind() -> None:
    with pytest.raises(ValueError, match="unknown embedder"):
        make_embedder("word2vec")


@pytest.mark.model
def test_local_embedder_ranks_by_meaning() -> None:
    e = LocalEmbedder()
    assert (e.dim, e.max_tokens) == (384, 512)
    docs = e.embed_documents(["How to reset a forgotten password", "Printer toner is empty"])
    q = e.embed_query("I can't remember my login secret")
    assert float(q @ docs[0]) > float(q @ docs[1])
    assert e.count_tokens("hello world") == 2


def test_store_round_trip_with_acl_filter(conn: psycopg.Connection[Any]) -> None:
    docs: list[Document] = [
        make_doc("VPN gateway failover steps", "open-doc", ("all-staff",)),
        make_doc("Project Kestrel budget figures", "fin-doc", ("finance",)),
    ]
    emb = HashEmbedder(dim=64)
    chunks = chunk_corpus(docs, max_tokens=50, count=emb.count_tokens)
    store = PgVectorStore(conn, "test_ragkit_store", emb.dim)
    store.reset()
    store.add(chunks, emb.embed_documents([c.text for c in chunks]), docs)
    store.build_index()

    assert store.count() == 2
    q = emb.embed_query("Kestrel budget")
    assert store.search(q, 1)[0].doc_id == "fin-doc"
    assert [h.doc_id for h in store.search(q, 5, groups=["all-staff"])] == ["open-doc"]
    assert [c[1] for c in store.all_chunks()] == ["open-doc", "fin-doc"]
    with pytest.raises(ValueError, match="2 chunks but 1 vectors"):
        store.add(chunks, emb.embed_documents(["x"]), docs)
    with pytest.raises(ValueError, match="invalid table name"):
        PgVectorStore(conn, "x; DROP TABLE y", 3)


def test_iterative_scan_returns_rows_an_hnsw_filter_would_hide(
    conn: psycopg.Connection[Any],
) -> None:
    """2,000 chunks, 5 readable by `security`. The index returns its 40 nearest rows, the filter
    removes them all, and without iterative scan the user gets nothing at all."""
    rng = np.random.default_rng(0)
    dim = 32
    docs = [make_doc("x", "pub", ("all-staff",)), make_doc("x", "sec", ("security",))]
    chunks = [Chunk("sec" if i < 5 else "pub", i, f"c{i}", "", 1) for i in range(2000)]
    store = PgVectorStore(conn, "test_ragkit_hnsw_trap", dim)
    store.reset()
    store.add(chunks, rng.normal(size=(2000, dim)).astype(np.float32), docs)
    store.build_index()
    conn.execute("ANALYZE test_ragkit_hnsw_trap")
    conn.execute("SET enable_seqscan = off")  # small tables use a seq scan; force the index
    try:
        q = rng.normal(size=dim).astype(np.float32)
        assert store.search(q, 5, groups=["security"], iterative_scan=False) == []
        found = store.search(q, 5, groups=["security"])
        assert [h.doc_id for h in found] == ["sec"] * 5
        assert store.readable_chunk_ids(["security"]) == {f"sec#{i}" for i in range(5)}
    finally:
        conn.execute("RESET enable_seqscan")
