import asyncio
from collections.abc import AsyncIterator
from typing import Protocol


class ChatModel(Protocol):
    """Anything that can stream a reply token by token.

    The route depends on this interface, not on a concrete class, so the fake model below
    can be swapped for an Amazon Bedrock client in M05 without touching the route.
    """

    def stream(self, message: str) -> AsyncIterator[str]: ...


class FakeChatModel:
    def __init__(self, delay_seconds: float = 0.05) -> None:
        self.delay_seconds = delay_seconds

    async def stream(self, message: str) -> AsyncIterator[str]:
        reply = f"You said: {message}. This is a fake model; swap in Amazon Bedrock in M05."
        for i, word in enumerate(reply.split(" ")):
            # asyncio.sleep, never time.sleep: a blocking sleep would freeze every other request.
            await asyncio.sleep(self.delay_seconds)
            yield word if i == 0 else f" {word}"
