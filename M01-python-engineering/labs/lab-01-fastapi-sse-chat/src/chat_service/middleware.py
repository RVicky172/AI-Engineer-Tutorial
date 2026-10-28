import re
import time
import uuid

import structlog
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

REQUEST_ID_HEADER = "x-request-id"
# Only accept caller-supplied IDs that are safe to put in logs and headers.
# Anything else (newlines, huge values) could be used for log injection, so we replace it.
_VALID_REQUEST_ID = re.compile(r"[A-Za-z0-9._-]{1,64}")

log = structlog.get_logger()


class RequestContextMiddleware:
    """Pure ASGI middleware: request ID, log context, and one access-log line per request.

    Why not `@app.middleware("http")` / BaseHTTPMiddleware? Pure ASGI middleware wraps the
    raw `send`, so it sees the true end of a streaming response (good for duration) and adds
    no extra task layer around the app.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = _incoming_request_id(scope) or uuid.uuid4().hex
        # Also store it on request.state: the 500 handler runs *outside* this middleware,
        # after the log context below has been cleared, and still needs the ID.
        scope.setdefault("state", {})["request_id"] = request_id
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id, method=scope["method"], path=scope["path"]
        )

        start = time.perf_counter()
        status_code = 500  # stays 500 if the app raises before sending a response

        async def send_with_request_id(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                # Set, not append: error handlers also set it, and a duplicate header would
                # reach the client as "id, id" (the tests caught exactly that bug).
                MutableHeaders(scope=message)[REQUEST_ID_HEADER] = request_id
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            log.info(
                "request.completed",
                status_code=status_code,
                duration_ms=round((time.perf_counter() - start) * 1000, 1),
            )
            structlog.contextvars.clear_contextvars()


def _incoming_request_id(scope: Scope) -> str | None:
    for name, value in scope["headers"]:
        if name == REQUEST_ID_HEADER.encode():
            candidate: str = value.decode("latin-1")
            return candidate if _VALID_REQUEST_ID.fullmatch(candidate) else None
    return None
