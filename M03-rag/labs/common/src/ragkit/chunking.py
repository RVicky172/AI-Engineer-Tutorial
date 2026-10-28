"""Heading-aware chunking to a token budget.

A document is cut into blocks (paragraphs, list items, whole tables, a heading glued to the block
after it), then blocks are packed into chunks of at most `max_tokens`. Blocks are only split when a
single block is larger than the budget: first by line, then by words. Tables therefore stay whole
whenever they fit, and a heading is never the last line of a chunk.

Every chunk starts with a contextual header (the document title), so a chunk that says "Restart
it with systemctl" still says *what* it is about when it's retrieved alone.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass

from ragkit.corpus import Document

TokenCounter = Callable[[str], int]
HEADING = re.compile(r"^#{1,6}\s+(.*)$")


@dataclass(frozen=True)
class Chunk:
    doc_id: str
    index: int
    text: str  # header + body: exactly what is embedded and shown to the model
    section: str
    tokens: int

    @property
    def chunk_id(self) -> str:
        return f"{self.doc_id}#{self.index}"


def word_count(text: str) -> int:
    """A rough token counter for tests and for embedders that don't expose a tokenizer."""
    return len(text.split())


def blocks(text: str) -> list[tuple[str, str]]:
    """(section, block) pairs. Blank lines separate blocks; consecutive table rows stay together;
    a heading is merged into the block that follows it."""
    out: list[tuple[str, str]] = []
    section = ""
    pending_heading = ""
    current: list[str] = []

    def flush() -> None:
        nonlocal pending_heading
        if current:
            body = "\n".join(current)
            out.append((section, f"{pending_heading}\n{body}" if pending_heading else body))
            pending_heading = ""
            current.clear()

    for line in text.splitlines():
        if match := HEADING.match(line):
            flush()
            if pending_heading:  # two headings in a row: keep both
                line = f"{pending_heading}\n{line}"
            section, pending_heading = match.group(1).strip(), line
        elif not line.strip():
            flush()
        elif current and current[-1].startswith("|") != line.startswith("|"):
            flush()  # a table starts or ends: separate block
            current.append(line)
        else:
            current.append(line)
    flush()
    if pending_heading:
        out.append((section, pending_heading))
    return out


def _word_windows(text: str, budget: int, count: TokenCounter) -> list[str]:
    pieces: list[str] = []
    current: list[str] = []
    for word in text.split():
        if current and count(" ".join([*current, word])) > budget:
            pieces.append(" ".join(current))
            current = []
        current.append(word)
    if current:
        pieces.append(" ".join(current))
    return pieces


def _split_oversized(block: str, budget: int, count: TokenCounter) -> list[str]:
    """Split one block that doesn't fit into groups of whole lines. A table's header and
    separator rows are repeated in every piece: '| AR_DUNNING | 03:00 | no |' means nothing
    without its column names. A single line longer than the budget is cut into word windows."""
    if count(block) <= budget:
        return [block]
    lines = block.splitlines()
    is_table = len(lines) > 2 and lines[0].startswith("|") and lines[1].startswith("|-")
    header = lines[:2] if is_table else []
    pieces: list[str] = []
    current: list[str] = []
    for line in lines[len(header) :]:
        if current and count("\n".join([*header, *current, line])) > budget:
            pieces.append("\n".join([*header, *current]))
            current = []
        current.append(line)
    if current:
        pieces.append("\n".join([*header, *current]))
    return [
        part
        for piece in pieces
        for part in ([piece] if count(piece) <= budget else _word_windows(piece, budget, count))
    ]


def _tail(text: str, tokens: int, count: TokenCounter) -> str:
    """About the last `tokens` tokens of text, as whole lines: a word-level cut produces
    fragments like 'get duplicate reminders | |' from the middle of a table row. Falls back to
    words only when the last line alone is much longer than the overlap."""
    if tokens <= 0:
        return ""
    kept: list[str] = []
    for line in reversed(text.splitlines()):
        kept.insert(0, line)
        if count("\n".join(kept)) >= tokens:
            break
    tail = "\n".join(kept).strip()
    if count(tail) <= 2 * tokens:
        return tail
    tail = kept[-1].strip()  # whole lines overshoot: the last line alone, if it is short enough
    if count(tail) <= 2 * tokens:
        return tail
    words = tail.split()
    for start in range(len(words) - 1, -1, -1):
        if count(" ".join(words[start:])) >= tokens:
            return " ".join(words[start:])
    return tail  # pragma: no cover - the loop always reaches `tokens` for a long line


def chunk_document(
    doc: Document,
    *,
    max_tokens: int,
    overlap_tokens: int = 0,
    count: TokenCounter = word_count,
) -> list[Chunk]:
    header = f"{doc.title}\n\n"
    budget = max_tokens - count(header)
    if budget < 20:
        raise ValueError(f"max_tokens={max_tokens} leaves no room after the header")
    # Pieces of a split block leave room for the overlap (a whole-line tail can be up to twice
    # overlap_tokens); otherwise every piece fills the budget and the overlap is silently dropped
    # exactly where it matters: inside long blocks.
    piece_budget = max(budget - 2 * overlap_tokens, budget // 2)
    pieces = [
        (section, piece)
        for section, block in blocks(doc.text)
        for piece in _split_oversized(block, piece_budget, count)
    ]
    chunks: list[Chunk] = []
    body: list[str] = []
    section: str | None = None  # the section of the chunk's first new block (not the overlap)

    def emit() -> None:
        text = header + "\n\n".join(body)
        chunks.append(Chunk(doc.doc_id, len(chunks), text, section or "", count(text)))

    for piece_section, piece in pieces:
        if section is not None and count("\n\n".join([*body, piece])) > budget:
            previous = "\n\n".join(body)
            emit()
            tail = _tail(previous, overlap_tokens, count)
            # the overlap only carries context; it must never push a chunk over the budget
            body = [tail] if tail and count(f"{tail}\n\n{piece}") <= budget else []
            section = None
        if section is None:
            section = piece_section
        body.append(piece)
    if section is not None:
        emit()
    return chunks


def chunk_corpus(
    docs: list[Document], *, max_tokens: int, overlap_tokens: int = 0, count: TokenCounter
) -> list[Chunk]:
    return [
        chunk
        for doc in docs
        for chunk in chunk_document(
            doc, max_tokens=max_tokens, overlap_tokens=overlap_tokens, count=count
        )
    ]
