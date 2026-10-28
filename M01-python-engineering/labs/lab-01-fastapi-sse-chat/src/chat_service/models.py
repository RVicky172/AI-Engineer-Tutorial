from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    # extra="forbid": a typo like "mesage" becomes a 422 instead of being silently ignored.
    # str_strip_whitespace: "   " is stripped to "" and then fails min_length.
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    message: str = Field(min_length=1, max_length=4000)
    session_id: UUID


class ChatChunk(BaseModel):
    """Payload of one `token` SSE event. JSON keeps leading spaces and lets us add fields later."""

    index: int
    token: str


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


class ErrorBody(BaseModel):
    code: str
    message: str
    request_id: str | None = None
    details: list[dict[str, Any]] | None = None


class ErrorResponse(BaseModel):
    """Every error the API returns has this one shape, so clients need one parser."""

    error: ErrorBody
