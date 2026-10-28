import asyncio
import json
from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import Annotated

import structlog
from fastapi import Depends, FastAPI, Request
from sse_starlette import EventSourceResponse, ServerSentEvent

from chat_service.config import Settings
from chat_service.errors import register_error_handlers
from chat_service.llm import ChatModel, FakeChatModel
from chat_service.log import configure_logging
from chat_service.middleware import RequestContextMiddleware
from chat_service.models import ChatChunk, ChatRequest, ErrorResponse, HealthResponse

log = structlog.get_logger()


def create_app(settings: Settings | None = None, chat_model: ChatModel | None = None) -> FastAPI:
    """App factory: tests build an app with their own settings and model; nothing happens at
    import time. Run with: uvicorn chat_service.main:create_app --factory --app-dir src
    """
    settings = settings or Settings()
    configure_logging(settings.log_level, settings.log_json)

    app = FastAPI(title=settings.app_name, lifespan=_lifespan(settings))
    # Set here rather than in the lifespan: httpx's ASGITransport (used in tests) does not
    # run lifespan events. A real client holding connections would be created in the
    # lifespan and closed there; see NOTES.md.
    app.state.chat_model = chat_model or FakeChatModel(settings.token_delay_seconds)

    app.add_middleware(RequestContextMiddleware)
    register_error_handlers(app)

    @app.get("/health")
    async def health() -> HealthResponse:
        return HealthResponse()

    @app.post(
        "/chat",
        response_class=EventSourceResponse,
        responses={422: {"model": ErrorResponse}},
    )
    async def chat(
        body: ChatRequest, model: Annotated[ChatModel, Depends(get_chat_model)]
    ) -> EventSourceResponse:
        # Log the size, not the content: user messages can contain personal data.
        log.info("chat.started", session_id=str(body.session_id), message_chars=len(body.message))
        return EventSourceResponse(stream_events(body, model))

    return app


def get_chat_model(request: Request) -> ChatModel:
    """Dependency, so tests can swap the model with app.dependency_overrides."""
    model: ChatModel = request.app.state.chat_model
    return model


async def stream_events(body: ChatRequest, model: ChatModel) -> AsyncIterator[ServerSentEvent]:
    """token* then exactly one of: done | error.

    Once the first byte is sent the HTTP status is already 200, so an exception can no longer
    become a 500. Failures mid-stream must be reported *inside* the stream as an error event.
    """
    sent = 0
    try:
        async for token in model.stream(body.message):
            chunk = ChatChunk(index=sent, token=token)
            yield ServerSentEvent(event="token", data=chunk.model_dump_json())
            sent += 1
    except asyncio.CancelledError:
        # sse-starlette cancels this generator when the client disconnects. Re-raise so the
        # cancellation propagates and the upstream model call stops (no wasted tokens).
        log.info("chat.client_disconnected", tokens_sent=sent)
        raise
    except Exception:
        log.exception("chat.stream_failed", tokens_sent=sent)
        error = {"code": "stream_failed", "message": "The model stopped unexpectedly."}
        yield ServerSentEvent(event="error", data=json.dumps(error))
        return
    log.info("chat.completed", tokens_sent=sent)
    yield ServerSentEvent(event="done", data=json.dumps({"tokens": sent}))


def _lifespan(settings: Settings) -> Callable[[FastAPI], AbstractAsyncContextManager[None]]:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        log.info("app.startup", app_name=settings.app_name)
        yield
        log.info("app.shutdown")

    return lifespan
