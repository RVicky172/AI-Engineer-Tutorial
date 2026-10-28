from anthropic.types import Message, ToolUseBlock


def text_of(message: Message) -> str:
    """All text blocks joined. A response can also hold thinking and tool_use blocks,
    so never assume `content[0]` is the answer."""
    return "".join(block.text for block in message.content if block.type == "text")


def tool_uses(message: Message) -> list[ToolUseBlock]:
    return [block for block in message.content if block.type == "tool_use"]
