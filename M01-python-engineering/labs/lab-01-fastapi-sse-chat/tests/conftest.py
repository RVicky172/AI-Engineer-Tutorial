from collections.abc import AsyncIterator

import httpx
import pytest
from fastapi import FastAPI

from chat_service.config import Settings
from chat_service.llm import FakeChatModel
from chat_service.main import create_app


@pytest.fixture
def settings() -> Settings:
    # _env_file=None: a developer's local .env must never change test results.
    return Settings(_env_file=None, token_delay_seconds=0, log_json=True)  # type: ignore[call-arg]


@pytest.fixture
def app(settings: Settings) -> FastAPI:
    return create_app(settings, chat_model=FakeChatModel(delay_seconds=0))


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    # ASGITransport calls the app in-process: no server, no ports, fast and deterministic.
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


def parse_sse(text: str) -> list[tuple[str, str]]:
    """Turn an SSE body into [(event, data), ...]. Events are separated by a blank line."""
    events = []
    for block in text.replace("\r\n", "\n").strip().split("\n\n"):
        event, data = "message", []
        for line in block.split("\n"):
            if line.startswith("event:"):
                event = line.removeprefix("event:").strip()
            elif line.startswith("data:"):
                data.append(line.removeprefix("data:").removeprefix(" "))
        if data:
            events.append((event, "\n".join(data)))
    return events
