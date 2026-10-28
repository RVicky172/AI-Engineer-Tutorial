from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from chat_service.middleware import REQUEST_ID_HEADER
from chat_service.models import ErrorBody, ErrorResponse

log = structlog.get_logger()


def register_error_handlers(app: FastAPI) -> None:
    # The decorator form keeps each handler's precise exception type for mypy.
    app.exception_handler(RequestValidationError)(_validation_error)
    app.exception_handler(StarletteHTTPException)(_http_error)
    # Registering `Exception` makes Starlette's outermost ServerErrorMiddleware use this
    # handler for anything unhandled.
    app.exception_handler(Exception)(_unhandled_error)


def _error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: list[dict[str, Any]] | None = None,
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    body = ErrorResponse(
        error=ErrorBody(code=code, message=message, request_id=request_id, details=details)
    )
    response = JSONResponse(status_code=status_code, content=body.model_dump(exclude_none=True))
    if request_id:
        # Needed for 500s: they are sent outside our middleware, which normally adds it.
        response.headers[REQUEST_ID_HEADER] = request_id
    return response


async def _validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    details = [
        # loc looks like ("body", "message"); drop "body" so clients see the field name.
        {"field": ".".join(str(p) for p in err["loc"][1:]), "message": err["msg"]}
        for err in exc.errors()
    ]
    return _error_response(request, 422, "validation_error", "Request body is invalid.", details)


async def _http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return _error_response(request, exc.status_code, "http_error", str(exc.detail))


async def _unhandled_error(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    # The log context was cleared by the middleware already, so bind the ID explicitly.
    log.error("request.unhandled_error", request_id=request_id, exc_info=exc)
    # Never send exception text to the client: it can leak internals (paths, SQL, secrets).
    return _error_response(
        request,
        500,
        "internal_error",
        "Something went wrong. Quote the request_id when reporting this.",
    )
