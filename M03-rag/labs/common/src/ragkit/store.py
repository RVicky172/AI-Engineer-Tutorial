"""Chunks in PostgreSQL + pgvector: one table per configuration, an HNSW index for cosine
distance, and access control inside the SQL."""

import json
import os
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import psycopg
from pgvector.psycopg import register_vector
from psycopg import sql

from ragkit.chunking import Chunk
from ragkit.corpus import Document
from ragkit.embedding import Vectors

DEFAULT_DSN = "postgresql://rag:rag@localhost:5432/rag"  # docker-compose.yml; local only
TABLE_NAME = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")


def connect(dsn: str | None = None) -> psycopg.Connection[Any]:
    conn = psycopg.connect(dsn or os.environ.get("PG_DSN") or DEFAULT_DSN, autocommit=True)
    conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    register_vector(conn)
    return conn


@dataclass(frozen=True)
class Hit:
    chunk_id: str
    doc_id: str
    text: str
    score: float  # cosine similarity, 1 = identical direction


class PgVectorStore:
    def __init__(self, conn: psycopg.Connection[Any], table: str, dim: int) -> None:
        if not TABLE_NAME.match(table):
            # identifiers can't be query parameters, so validate before building SQL
            raise ValueError(f"invalid table name {table!r}")
        self.conn, self.dim = conn, dim
        self.table = sql.Identifier(table)
        self.name = table

    def reset(self) -> None:
        self.conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(self.table))
        self.conn.execute(
            sql.SQL(
                """CREATE TABLE {} (
                    id bigserial PRIMARY KEY,
                    chunk_id text UNIQUE NOT NULL,
                    doc_id text NOT NULL,
                    chunk_text text NOT NULL,
                    metadata jsonb NOT NULL,
                    allowed_groups text[] NOT NULL,
                    embedding vector({}) NOT NULL
                )"""
            ).format(self.table, sql.Literal(self.dim))
        )

    def add(self, chunks: Sequence[Chunk], vectors: Vectors, docs: Sequence[Document]) -> None:
        """ACL metadata is copied from the document onto every chunk at ingestion: retrieval
        works on chunks, so a chunk must carry its own permissions."""
        if len(chunks) != len(vectors):
            raise ValueError(f"{len(chunks)} chunks but {len(vectors)} vectors")
        by_id = {d.doc_id: d for d in docs}
        rows = [
            (
                c.chunk_id,
                c.doc_id,
                c.text,
                json.dumps({**by_id[c.doc_id].metadata, "section": c.section, "tokens": c.tokens}),
                list(by_id[c.doc_id].allowed_groups),
                vec,
            )
            for c, vec in zip(chunks, vectors, strict=True)
        ]
        with self.conn.cursor() as cur:
            cur.executemany(
                sql.SQL(
                    "INSERT INTO {} (chunk_id, doc_id, chunk_text, metadata, allowed_groups, "
                    "embedding) VALUES (%s, %s, %s, %s, %s, %s)"
                ).format(self.table),
                rows,
            )

    def build_index(self) -> None:
        """Approximate nearest neighbour index. Build it after loading: inserting into an
        existing HNSW index is much slower than building it once."""
        self.conn.execute(
            sql.SQL("CREATE INDEX ON {} USING hnsw (embedding vector_cosine_ops)").format(
                self.table
            )
        )

    def count(self) -> int:
        row = self.conn.execute(sql.SQL("SELECT count(*) FROM {}").format(self.table)).fetchone()
        return int(row[0]) if row else 0

    def search(
        self, query: Vectors, k: int = 5, *, groups: Sequence[str] | None = None
    ) -> list[Hit]:
        """`groups=None` means no access control (admin / evaluation view). With groups, the
        filter is part of the query, so rows the user may not read never leave the database."""
        where = sql.SQL("")
        params: list[Any] = [query]
        if groups is not None:
            where = sql.SQL("WHERE allowed_groups && %s")
            params.append(list(groups))
        params += [query, k]
        rows = self.conn.execute(
            sql.SQL(
                "SELECT chunk_id, doc_id, chunk_text, 1 - (embedding <=> %s) AS score "
                "FROM {} {} ORDER BY embedding <=> %s LIMIT %s"
            ).format(self.table, where),
            params,
        ).fetchall()
        return [Hit(r[0], r[1], r[2], float(r[3])) for r in rows]

    def all_chunks(self) -> list[tuple[str, str, str]]:
        """(chunk_id, doc_id, text) for every row, in insertion order: for BM25."""
        rows = self.conn.execute(
            sql.SQL("SELECT chunk_id, doc_id, chunk_text FROM {} ORDER BY id").format(self.table)
        ).fetchall()
        return [(r[0], r[1], r[2]) for r in rows]
