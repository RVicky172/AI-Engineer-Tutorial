from pathlib import Path

import pytest

from ragkit.corpus import Document, load_corpus, load_markdown, load_pdf
from ragkit.golden import check_evidence, load_golden
from tests.conftest import LABS


def test_corpus_is_the_right_size_with_metadata_on_every_doc(docs: list[Document]) -> None:
    assert 50 <= len(docs) <= 100
    for d in docs:
        assert d.title and d.text and d.allowed_groups, d.doc_id
        assert d.metadata["format"] in ("md", "pdf")
    groups = {g for d in docs for g in d.allowed_groups}
    assert {"all-staff", "it-ops", "finance", "hr", "security"} <= groups


def test_pdfs_are_extracted_and_keep_sidecar_metadata(docs: list[Document]) -> None:
    pdfs = [d for d in docs if d.metadata["format"] == "pdf"]
    assert len(pdfs) == 3
    travel = next(d for d in pdfs if d.doc_id == "travel-expense-policy")
    assert "up to INR 9,000" in travel.text
    assert travel.allowed_groups == ("all-staff",)


def test_metadata_errors_name_the_file(tmp_path: Path) -> None:
    bad_yaml = tmp_path / "a.md"
    bad_yaml.write_text("---\ntitle: First day: oops\nallowed_groups: [x]\n---\nbody")
    with pytest.raises(ValueError, match=r"a\.md: invalid metadata YAML"):
        load_markdown(bad_yaml)

    no_groups = tmp_path / "b.md"
    no_groups.write_text("---\ntitle: B\n---\nbody")
    with pytest.raises(ValueError, match=r"b\.md: metadata is missing \['allowed_groups'\]"):
        load_markdown(no_groups)

    empty_groups = tmp_path / "c.md"
    empty_groups.write_text("---\ntitle: C\nallowed_groups: []\n---\nbody")
    with pytest.raises(ValueError, match="non-empty list"):
        load_markdown(empty_groups)

    list_meta = tmp_path / "d.md"
    list_meta.write_text("---\n- a\n---\nbody")
    with pytest.raises(ValueError, match="mapping"):
        load_markdown(list_meta)

    no_front = tmp_path / "e.md"
    no_front.write_text("# just text")
    with pytest.raises(ValueError, match="no front matter"):
        load_markdown(no_front)


def test_pdf_without_sidecar_and_duplicate_ids_are_rejected(tmp_path: Path) -> None:
    pdf = LABS / "corpus" / "vendor-sla-summary.pdf"
    lonely = tmp_path / "x.pdf"
    lonely.write_bytes(pdf.read_bytes())
    with pytest.raises(ValueError, match="sidecar"):
        load_pdf(lonely)

    (tmp_path / "x.pdf.meta.yaml").write_text("title: X\nallowed_groups: [a]\n")
    (tmp_path / "x.md").write_text("---\ntitle: X\nallowed_groups: [a]\n---\nbody")
    with pytest.raises(ValueError, match="duplicate doc ids"):
        load_corpus(tmp_path)


def test_golden_set_is_valid_against_the_corpus(docs: list[Document]) -> None:
    questions = load_golden(LABS / "golden.yaml", {d.doc_id for d in docs})
    check_evidence(questions, docs)  # every answer phrase exists in a relevant document
    assert len(questions) == 25
    readable = {d.doc_id: set(d.allowed_groups) for d in docs}
    for q in questions:
        for doc_id in q.relevant:  # Lab 03 asks as these groups: they must see the answer
            assert readable[doc_id] & set(q.groups), (q.id, doc_id)


def test_golden_set_problems_are_caught(tmp_path: Path, docs: list[Document]) -> None:
    def write(body: str) -> Path:
        path = tmp_path / "g.yaml"
        path.write_text(body)
        return path

    q = "  - {{id: {}, question: x, relevant: [{}], evidence: ['{}'], answer: a, groups: [g]}}\n"
    with pytest.raises(ValueError, match="duplicate"):
        load_golden(write("questions:\n" + q.format("a", "d", "e") * 2))
    with pytest.raises(ValueError, match="unknown documents"):
        load_golden(write("questions:\n" + q.format("a", "gone", "e")), {"kb-teams-audio"})
    wrong = load_golden(write("questions:\n" + q.format("a", "kb-teams-audio", "not there")))
    with pytest.raises(ValueError, match="evidence 'not there'"):
        check_evidence(wrong, docs)
