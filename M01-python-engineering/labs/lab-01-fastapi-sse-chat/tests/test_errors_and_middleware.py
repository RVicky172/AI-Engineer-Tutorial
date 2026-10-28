import json
import uuid

import httpx
import pytest
from fastapi import FastAPI


async def test_generates_request_id_when_missing(client: httpx.AsyncClient) -> None:
    response = await client.get("/health")
    assert len(response.headers["x-request-id"]) == 32  # uuid4 hex


async def test_echoes_valid_incoming_request_id(client: httpx.AsyncClient) -> None:
    response = await client.get("/health", headers={"x-request-id": "abc-123"})
    assert response.headers["x-request-id"] == "abc-123"


@pytest.mark.parametrize("bad_id", ["has space", "x" * 65, "line\tbreak", 'quote"id'])
async def test_replaces_unsafe_incoming_request_id(client: httpx.AsyncClient, bad_id: str) -> None:
    response = await client.get("/health", headers={"x-request-id": bad_id})
    assert response.headers["x-request-id"] != bad_id


async def test_unknown_route_uses_standard_error_shape(client: httpx.AsyncClient) -> None:
    response = await client.get("/nope")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "http_error"


async def test_unhandled_exception_returns_safe_500(app: FastAPI) -> None:
    @app.get("/boom")
    async def boom() -> None:
        raise ValueError("password=hunter2 leaked in an exception message")

    # raise_app_exceptions=False: Starlette re-raises after sending the 500 (so servers log
    # it); without this flag the test client would raise instead of returning the response.
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/boom", headers={"x-request-id": "req-500"})

    assert response.status_code == 500
    assert response.headers["x-request-id"] == "req-500"
    assert response.json()["error"] == {
        "code": "internal_error",
        "message": "Something went wrong. Quote the request_id when reporting this.",
        "request_id": "req-500",
    }
    assert "hunter2" not in response.text


async def test_every_log_line_in_a_request_has_the_request_id(
    client: httpx.AsyncClient, capsys: pytest.CaptureFixture[str]
) -> None:
    await client.post(
        "/chat",
        json={"message": "secret-ish user text", "session_id": str(uuid.uuid4())},
        headers={"x-request-id": "trace-me"},
    )

    lines = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    events = [line["event"] for line in lines]
    assert events == ["chat.started", "chat.completed", "request.completed"]
    assert all(line["request_id"] == "trace-me" for line in lines)
    assert lines[-1]["status_code"] == 200
    assert "secret-ish user text" not in json.dumps(lines)  # we log sizes, not content
