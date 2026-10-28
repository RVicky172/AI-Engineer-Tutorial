import asyncio
import json
import uuid
from collections.abc import AsyncIterator

import httpx
import pytest
from fastapi import FastAPI

from chat_service.main import get_chat_model, stream_events
from chat_service.models import ChatRequest
from tests.conftest import parse_sse

SESSION = str(uuid.uuid4())


async def test_health(client: httpx.AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_chat_streams_tokens_then_done(client: httpx.AsyncClient) -> None:
    response = await client.post("/chat", json={"message": "hello", "session_id": SESSION})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    events = parse_sse(response.text)
    tokens = [json.loads(data) for event, data in events if event == "token"]
    assert [t["index"] for t in tokens] == list(range(len(tokens)))
    assert "".join(t["token"] for t in tokens).startswith("You said: hello.")
    assert events[-1] == ("done", json.dumps({"tokens": len(tokens)}))


@pytest.mark.parametrize(
    ("payload", "bad_field"),
    [
        ({"session_id": SESSION}, "message"),
        ({"message": "", "session_id": SESSION}, "message"),
        ({"message": "   ", "session_id": SESSION}, "message"),
        ({"message": "x" * 4001, "session_id": SESSION}, "message"),
        ({"message": "hi", "session_id": "not-a-uuid"}, "session_id"),
        ({"message": "hi", "session_id": SESSION, "mesage": "typo"}, "mesage"),
    ],
    ids=["missing", "empty", "whitespace", "too-long", "bad-uuid", "unknown-field"],
)
async def test_chat_rejects_invalid_input(
    client: httpx.AsyncClient, payload: dict[str, str], bad_field: str
) -> None:
    response = await client.post("/chat", json=payload)

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert error["request_id"] == response.headers["x-request-id"]
    assert bad_field in [d["field"] for d in error["details"]]


class FailsAfterOneToken:
    async def stream(self, message: str) -> AsyncIterator[str]:
        yield "partial"
        raise RuntimeError("upstream model connection reset")


async def test_failure_mid_stream_sends_error_event(
    app: FastAPI, client: httpx.AsyncClient
) -> None:
    app.dependency_overrides[get_chat_model] = FailsAfterOneToken

    response = await client.post("/chat", json={"message": "hi", "session_id": SESSION})

    # The 200 was already sent with the first token, so the error must arrive as an event.
    assert response.status_code == 200
    events = parse_sse(response.text)
    assert [e for e, _ in events] == ["token", "error"]
    assert json.loads(events[1][1])["code"] == "stream_failed"
    assert "connection reset" not in response.text  # internal detail is not leaked


class HangsAfterOneToken:
    async def stream(self, message: str) -> AsyncIterator[str]:
        yield "first"
        await asyncio.Event().wait()  # simulates a slow model that never finishes
        yield "never"


async def test_client_disconnect_cancels_stream(capsys: pytest.CaptureFixture[str]) -> None:
    body = ChatRequest(message="hi", session_id=uuid.UUID(SESSION))
    first_event = asyncio.Event()

    async def consume() -> None:
        async for _ in stream_events(body, HangsAfterOneToken()):
            first_event.set()

    task = asyncio.create_task(consume())
    await first_event.wait()
    task.cancel()  # this is what sse-starlette does when the client goes away
    with pytest.raises(asyncio.CancelledError):
        await task

    logs = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert {"event": "chat.client_disconnected", "tokens_sent": 1}.items() <= logs[-1].items()
