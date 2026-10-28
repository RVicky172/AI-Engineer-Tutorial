"""Second-stage rankers. A bi-encoder (the embedder) scores query and chunk separately and
compares vectors; a cross-encoder reads the pair together, which is far more accurate and far
too slow to run over a whole corpus. Hence: retrieve 20 cheaply, rerank to 5."""

import os
from collections.abc import Sequence
from typing import Any, Protocol

from ragkit.hybrid import tokenize
from ragkit.store import Hit


class Reranker(Protocol):
    name: str

    def rerank(self, query: str, hits: Sequence[Hit], k: int) -> list[Hit]: ...


def _reorder(hits: Sequence[Hit], scores: Sequence[float], k: int) -> list[Hit]:
    """Stable: equal scores keep the first-stage order."""
    ranked = sorted(range(len(hits)), key=lambda i: -scores[i])[:k]
    return [Hit(hits[i].chunk_id, hits[i].doc_id, hits[i].text, float(scores[i])) for i in ranked]


class CrossEncoderReranker:
    """Option A: a local cross-encoder trained on MS MARCO passage ranking (22M params)."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2") -> None:
        os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
        from sentence_transformers import CrossEncoder

        self._model = CrossEncoder(model_name)
        self.name = model_name

    def rerank(self, query: str, hits: Sequence[Hit], k: int) -> list[Hit]:
        if not hits:
            return []
        scores = self._model.predict([(query, h.text) for h in hits], batch_size=32)
        return _reorder(hits, [float(s) for s in scores], k)


class BedrockReranker:
    """Option B: a Bedrock rerank model (Amazon Rerank or Cohere Rerank) through the
    bedrock-agent-runtime Rerank API. Billed per query; available in a few regions only, so
    check the model's regional availability first."""

    def __init__(self, model_arn: str, client: Any = None, *, region: str | None = None) -> None:
        if client is None:
            import boto3

            client = boto3.client("bedrock-agent-runtime", region_name=region)
        self._client = client
        self.model_arn = model_arn
        self.name = model_arn.rsplit("/", 1)[-1]

    def rerank(self, query: str, hits: Sequence[Hit], k: int) -> list[Hit]:
        if not hits:
            return []
        response = self._client.rerank(
            queries=[{"type": "TEXT", "textQuery": {"text": query}}],
            sources=[
                {
                    "type": "INLINE",
                    "inlineDocumentSource": {"type": "TEXT", "textDocument": {"text": h.text}},
                }
                for h in hits
            ],
            rerankingConfiguration={
                "type": "BEDROCK_RERANKING_MODEL",
                "bedrockRerankingConfiguration": {
                    "numberOfResults": min(k, len(hits)),
                    "modelConfiguration": {"modelArn": self.model_arn},
                },
            },
        )
        # results come back sorted by relevance, each pointing at the index of its source
        return [
            Hit(
                hits[r["index"]].chunk_id,
                hits[r["index"]].doc_id,
                hits[r["index"]].text,
                float(r["relevanceScore"]),
            )
            for r in response["results"]
        ]


class LexicalReranker:
    """Query-term overlap. Deterministic and instant: for tests, and as a sanity baseline a
    real reranker must beat."""

    name = "lexical-overlap"

    def rerank(self, query: str, hits: Sequence[Hit], k: int) -> list[Hit]:
        terms = set(tokenize(query))
        return _reorder(hits, [len(terms & set(tokenize(h.text))) for h in hits], k)


def make_reranker(kind: str, **kwargs: Any) -> Reranker:
    if kind == "cross-encoder":
        return CrossEncoderReranker(**kwargs)
    if kind == "bedrock":
        return BedrockReranker(**kwargs)
    if kind == "lexical":
        return LexicalReranker()
    raise ValueError(f"unknown reranker {kind!r}: use cross-encoder, bedrock or lexical")
