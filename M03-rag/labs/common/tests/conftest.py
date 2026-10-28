from collections.abc import Iterator
from pathlib import Path
from typing import Any

import psycopg
import pytest

from ragkit.corpus import Document, load_corpus
from ragkit.store import connect

LABS = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def docs() -> list[Document]:
    return load_corpus(LABS / "corpus")


@pytest.fixture(scope="session")
def conn() -> Iterator[psycopg.Connection[Any]]:
    """The docker-compose pgvector database. Start it with `docker compose up -d` in labs/."""
    try:
        connection = connect()
    except psycopg.OperationalError as exc:
        pytest.skip(f"pgvector not reachable ({exc}); run `docker compose up -d` in labs/")
    yield connection
    connection.close()


def make_doc(text: str, doc_id: str = "d1", groups: tuple[str, ...] = ("all-staff",)) -> Document:
    return Document(doc_id, "Title", text, groups, {"format": "md"}, Path(f"{doc_id}.md"))
