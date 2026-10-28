import pytest

from ragkit.chunking import blocks, chunk_corpus, chunk_document, word_count
from ragkit.corpus import Document
from tests.conftest import make_doc

TABLE = "| A | B |\n|---|---|\n" + "\n".join(
    f"| row{i} | value {i} with words |" for i in range(12)
)


@pytest.mark.parametrize("size", [40, 64, 128, 256])
def test_no_chunk_exceeds_the_budget_on_the_real_corpus(docs: list[Document], size: int) -> None:
    chunks = chunk_corpus(docs, max_tokens=size, overlap_tokens=size // 8, count=word_count)
    assert all(c.tokens <= size for c in chunks)
    assert len({c.chunk_id for c in chunks}) == len(chunks)


def test_every_word_of_a_document_lands_in_some_chunk(docs: list[Document]) -> None:
    doc = next(d for d in docs if d.doc_id == "rb-major-incident-process")
    chunks = chunk_document(doc, max_tokens=60, count=word_count)
    seen = {w for c in chunks for w in c.text.split()}
    assert set(doc.text.split()) <= seen


def test_blocks_glue_headings_to_their_content_and_keep_tables_whole() -> None:
    text = "# Title\n\nIntro line.\n\n## Steps\n### Detail\n1. one\n2. two\n" + TABLE + "\n\nEnd."
    out = blocks(text)
    assert out[0] == ("Title", "# Title\nIntro line.")
    assert out[1] == ("Detail", "## Steps\n### Detail\n1. one\n2. two")
    assert out[2][1].startswith("| A | B |") and out[2][1].count("\n") == 13
    assert out[3] == ("Detail", "End.")
    assert blocks("text\n## Dangling") == [("", "text"), ("Dangling", "## Dangling")]


def test_a_split_table_repeats_its_header_in_every_piece() -> None:
    chunks = chunk_document(make_doc(TABLE), max_tokens=40, count=word_count)
    assert len(chunks) > 1
    for c in chunks:
        assert "| A | B |\n|---|---|" in c.text
        assert c.text.startswith("Title\n\n")  # contextual header


def test_overlap_repeats_whole_lines_from_the_previous_chunk() -> None:
    text = "\n".join(f"Line {i} has five words." for i in range(30))
    first, second, *_ = chunk_document(
        make_doc(text), max_tokens=40, overlap_tokens=6, count=word_count
    )
    overlap = second.text.split("\n\n")[1]  # the block right after the header
    assert overlap.endswith(first.text.splitlines()[-1])
    assert all(line.startswith("Line ") for line in overlap.splitlines())  # no half lines


def test_overlap_falls_back_to_words_for_one_very_long_line() -> None:
    words = " ".join(f"w{i}" for i in range(100))
    _, second, *_ = chunk_document(
        make_doc(f"{words}\n\nnext"), max_tokens=60, overlap_tokens=5, count=word_count
    )
    assert second.text.split("\n\n", 1)[1].split()[0].startswith("w")


def test_overlap_never_pushes_a_chunk_over_the_budget() -> None:
    text = "short\n\n" + " ".join(f"x{i}" for i in range(55))
    chunks = chunk_document(make_doc(text), max_tokens=58, overlap_tokens=10, count=word_count)
    assert all(c.tokens <= 58 for c in chunks)


def test_sections_and_ids_are_recorded() -> None:
    text = "# A\n" + "a " * 30 + "\n\n## B\n" + "b " * 30
    chunks = chunk_document(make_doc(text), max_tokens=40, count=word_count)
    assert [c.section for c in chunks] == ["A", "B"]
    assert [c.chunk_id for c in chunks] == ["d1#0", "d1#1"]


def test_budget_must_leave_room_after_the_header() -> None:
    with pytest.raises(ValueError, match="no room"):
        chunk_document(make_doc("x"), max_tokens=10, count=word_count)
