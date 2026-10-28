from typing import Any, Protocol, cast

from anthropic import Anthropic, AnthropicBedrockMantle
from anthropic.types import Message

from llm_common.settings import Settings


class MessagesAPI(Protocol):
    """The slice of the SDK the labs use: `client.messages.create(...)` without streaming.
    The real `client.messages` and `FakeMessages` both fit, so lab code never knows which."""

    def create(self, **kwargs: Any) -> Message: ...


def make_messages_api(settings: Settings, *, max_retries: int = 2) -> MessagesAPI:
    """Both providers serve the same Messages API, so the labs run unchanged on either.
    M05 covers Bedrock's own Converse API, which has a different request shape."""
    client: Anthropic | AnthropicBedrockMantle
    if settings.provider == "bedrock":
        client = AnthropicBedrockMantle(
            aws_region=settings.aws_region,
            aws_profile=settings.aws_profile,
            max_retries=max_retries,
        )
    else:
        client = Anthropic(max_retries=max_retries)
    # create() is overloaded (stream=True returns a Stream). The labs never stream,
    # so the narrower Protocol is accurate for every call they make.
    return cast(MessagesAPI, client.messages)
