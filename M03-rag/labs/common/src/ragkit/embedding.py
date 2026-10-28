"""Embedders behind one small interface. Documents and queries MUST use the same embedder: a
vector from one model means nothing in another model's space, so changing the model means
re-embedding the whole corpus."""

import hashlib
import json
import os
import re
from collections.abc import Sequence
from typing import Any, Protocol

import numpy as np
from numpy.typing import NDArray

Vectors = NDArray[np.float32]
WORD = re.compile(r"[a-z0-9]+")


class Embedder(Protocol):
    name: str
    dim: int
    max_tokens: int  # longer input is silently truncated by the model

    def count_tokens(self, text: str) -> int: ...
    def embed_documents(self, texts: Sequence[str]) -> Vectors: ...
    def embed_query(self, text: str) -> Vectors: ...


class LocalEmbedder:
    """sentence-transformers on this machine: free, private, no network after the first
    download. bge models want an instruction prefix on queries (not on documents)."""

    QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5", device: str | None = None):
        os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")  # Windows cache noise
        from sentence_transformers import SentenceTransformer  # slow import: only when used

        self._model = SentenceTransformer(model_name, device=device)
        self.name = model_name
        dim = self._model.get_embedding_dimension()
        self.dim = int(dim) if dim else 0
        self.max_tokens = int(self._model.max_seq_length or 1_000_000)  # None: no limit

    def count_tokens(self, text: str) -> int:
        ids = self._model.tokenizer(text, add_special_tokens=False, verbose=False)["input_ids"]
        return len(ids)

    def _encode(self, texts: Sequence[str]) -> Vectors:
        vectors = self._model.encode(
            list(texts), batch_size=32, normalize_embeddings=True, convert_to_numpy=True
        )
        return np.asarray(vectors, dtype=np.float32)

    def embed_documents(self, texts: Sequence[str]) -> Vectors:
        return self._encode(texts)

    def embed_query(self, text: str) -> Vectors:
        return np.asarray(self._encode([self.QUERY_PREFIX + text])[0], dtype=np.float32)


class TitanEmbedder:
    """Amazon Titan Text Embeddings V2 on Bedrock: the model Knowledge Bases uses by default.
    Billed per input token. One text per call (the API has no batch input)."""

    name = "amazon.titan-embed-text-v2:0"
    max_tokens = 8192

    def __init__(self, client: Any = None, *, region: str | None = None, dim: int = 1024):
        if client is None:
            import boto3

            client = boto3.client("bedrock-runtime", region_name=region)
        self._client = client
        self.dim = dim  # 256, 512 or 1024

    def count_tokens(self, text: str) -> int:
        """Titan has no public tokenizer; ~1 token per word piece is close enough for chunking.
        The exact count comes back in each response as inputTextTokenCount."""
        return len(re.findall(r"\w+|[^\w\s]", text))

    def _embed(self, text: str) -> list[float]:
        body = json.dumps({"inputText": text, "dimensions": self.dim, "normalize": True})
        response = self._client.invoke_model(
            modelId=self.name, body=body, contentType="application/json", accept="application/json"
        )
        embedding: list[float] = json.loads(response["body"].read())["embedding"]
        return embedding

    def embed_documents(self, texts: Sequence[str]) -> Vectors:
        return np.asarray([self._embed(t) for t in texts], dtype=np.float32)

    def embed_query(self, text: str) -> Vectors:
        return np.asarray(self._embed(text), dtype=np.float32)


class HashEmbedder:
    """Deterministic bag-of-words vectors for tests: texts sharing words are close. No model,
    no network, identical on every machine."""

    name = "hash-bow"
    max_tokens = 100_000

    def __init__(self, dim: int = 256):
        self.dim = dim

    def count_tokens(self, text: str) -> int:
        return len(text.split())

    def _vector(self, text: str) -> NDArray[np.float32]:
        v = np.zeros(self.dim, dtype=np.float32)
        for word in WORD.findall(text.lower()):
            h = int.from_bytes(hashlib.md5(word.encode(), usedforsecurity=False).digest()[:4])
            v[h % self.dim] += 1.0 if h & (1 << 31) else -1.0
        norm = float(np.linalg.norm(v))
        return v / norm if norm else v

    def embed_documents(self, texts: Sequence[str]) -> Vectors:
        return np.asarray([self._vector(t) for t in texts], dtype=np.float32)

    def embed_query(self, text: str) -> Vectors:
        return self._vector(text)


def make_embedder(kind: str, **kwargs: Any) -> Embedder:
    if kind == "local":
        return LocalEmbedder(**kwargs)
    if kind == "titan":
        return TitanEmbedder(**kwargs)
    if kind == "hash":
        return HashEmbedder(**kwargs)
    raise ValueError(f"unknown embedder {kind!r}: use local, titan or hash")
