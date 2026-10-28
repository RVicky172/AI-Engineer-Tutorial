import itertools
import json
import threading
from collections.abc import Callable, Iterable, Mapping
from typing import Any, cast

import httpx2
from anthropic import Anthropic, DefaultHttpxClient
from anthropic.types import Message

from llm_common.client import MessagesAPI

Responder = Callable[[dict[str, Any]], Message]
_ids = itertools.count(1)


def tool_use_block(
    name: str, tool_input: Mapping[str, Any], id: str | None = None
) -> dict[str, Any]:
    return {
        "type": "tool_use",
        "id": id or f"toolu_{next(_ids)}",
        "name": name,
        "input": tool_input,
    }


def make_message(
    *blocks: str | dict[str, Any],
    stop_reason: str | None = None,
    input_tokens: int = 100,
    output_tokens: int = 20,
    thinking_tokens: int = 0,
    cache_read_tokens: int = 0,
    stop_details: dict[str, Any] | None = None,
) -> Message:
    """Build a real SDK `Message`, so tests exercise the same types production code sees.
    Plain strings become text blocks; dicts are used as-is (see `tool_use_block`)."""
    content = [{"type": "text", "text": b} if isinstance(b, str) else b for b in blocks]
    if stop_reason is None:
        stop_reason = "tool_use" if any(b["type"] == "tool_use" for b in content) else "end_turn"
    return Message.model_validate(
        {
            "id": f"msg_{next(_ids)}",
            "type": "message",
            "role": "assistant",
            "model": "fake-model",
            "content": content,
            "stop_reason": stop_reason,
            "stop_sequence": None,
            "stop_details": stop_details,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cache_read_input_tokens": cache_read_tokens,
                "output_tokens_details": {"thinking_tokens": thinking_tokens},
            },
        }
    )


class FakeMessages:
    """Scripted stand-in for `client.messages`. Give it a list of replies (returned in order;
    an Exception in the list is raised) or a function that builds a reply from the request.
    Every request is recorded in `calls`, so tests can assert what was *sent*."""

    def __init__(self, script: Iterable[Message | Exception] | Responder) -> None:
        self.calls: list[dict[str, Any]] = []
        self._lock = threading.Lock()  # lab runners call the model from a thread pool
        if callable(script):
            self._responder: Responder | None = script
            self._queue: list[Message | Exception] = []
        else:
            self._responder = None
            self._queue = list(script)

    def create(self, **kwargs: Any) -> Message:
        with self._lock:
            self.calls.append(kwargs)
            if self._responder is not None:
                return self._responder(kwargs)
            if not self._queue:
                raise AssertionError(f"FakeMessages ran out of replies after {len(self.calls) - 1}")
            reply = self._queue.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


def real_sdk_messages(reply: Message) -> tuple[MessagesAPI, list[dict[str, Any]]]:
    """The real `Anthropic().messages`, wired to an in-memory HTTP transport. Fakes can't tell
    you the SDK rejects a keyword or how it serialises your request; this can, with no network
    and no spend. Returns the API and the list of JSON bodies it sent."""
    sent: list[dict[str, Any]] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        sent.append({**json.loads(request.content), "_headers": dict(request.headers)})
        return httpx2.Response(200, json=reply.model_dump(mode="json"))

    client = Anthropic(
        api_key="test-key",
        max_retries=0,
        http_client=DefaultHttpxClient(transport=httpx2.MockTransport(handler)),
    )
    return cast(MessagesAPI, client.messages), sent
