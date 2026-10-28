import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from regression.cases import Suite, load_suite
from regression.checks import FieldEquals, FieldIn
from regression.prompts import PromptStore
from tests.fakes import LAB, SUITE

STORE = PromptStore(LAB / "prompts")
CATEGORIES = re.findall(r"^([a-z-]+):", STORE.load("triage", "v2").text, flags=re.MULTILINE)


def test_store_lists_versions_numerically_and_follows_current(tmp_path: Path) -> None:
    task = tmp_path / "t"
    task.mkdir()
    for v in ("v1", "v2", "v10", "draft"):
        (task / f"{v}.md").write_text("x")
    (task / "CURRENT").write_text("v10\n")
    store = PromptStore(tmp_path)

    assert store.versions("t") == ["v1", "v2", "v10"]
    assert store.load("t").version == "v10"


def test_current_must_point_at_an_existing_version(tmp_path: Path) -> None:
    (tmp_path / "t").mkdir()
    (tmp_path / "t" / "v1.md").write_text("x")
    (tmp_path / "t" / "CURRENT").write_text("v3")
    with pytest.raises(ValueError, match="v3"):
        PromptStore(tmp_path).current("t")
    with pytest.raises(FileNotFoundError, match="versions"):
        PromptStore(tmp_path).load("t", "v9")


def test_front_matter_is_metadata_not_prompt(tmp_path: Path) -> None:
    (tmp_path / "t").mkdir()
    (tmp_path / "t" / "v1.md").write_text("---\nnote: first\n---\nYou triage.\n")
    (tmp_path / "t" / "v2.md").write_text("---\n- a list\n---\nx")
    prompt = PromptStore(tmp_path).load("t", "v1")

    assert (prompt.text, prompt.note) == ("You triage.", "first")
    assert len(prompt.sha) == 12
    with pytest.raises(ValueError, match="mapping"):
        PromptStore(tmp_path).load("t", "v2")


@pytest.mark.parametrize("version", STORE.versions("triage"))
def test_real_prompts_are_clean_and_name_every_category(version: str) -> None:
    prompt = STORE.load("triage", version)
    assert prompt.note
    assert "\\\n" not in prompt.text  # a Python line continuation pasted into Markdown
    assert "---" not in prompt.text  # front matter fully stripped
    for category in CATEGORIES:
        assert category in prompt.text


def test_current_triage_prompt_is_v2() -> None:
    assert STORE.current("triage") == "v2"
    assert len(CATEGORIES) == 7


def test_suite_has_twenty_cases_each_pinning_category_and_priority() -> None:
    assert SUITE.task == "triage"
    assert len(SUITE.cases) == 20
    for case in SUITE.cases:
        fields = {c.field for c in case.checks if isinstance(c, FieldEquals | FieldIn)}
        assert {"category", "priority"} <= fields, case.id


def test_labels_use_only_values_the_prompt_allows() -> None:
    for case in SUITE.cases:
        for check in case.checks:
            values = (
                [check.value] if isinstance(check, FieldEquals) else getattr(check, "values", [])
            )
            field = getattr(check, "field", None)
            if field == "category":
                assert set(values) <= set(CATEGORIES), case.id
            if field == "priority":
                assert set(values) <= {"P1", "P2", "P3", "P4"}, case.id


def test_lenient_labels_stay_rare() -> None:
    lenient = [c.id for c in SUITE.cases for k in c.checks if isinstance(k, FieldIn)]
    assert len(lenient) <= 3, lenient


def test_suite_rejects_duplicates_and_unknown_check_types() -> None:
    case = {"id": "a", "input": "x", "checks": [{"type": "json_valid"}]}
    with pytest.raises(ValidationError, match="duplicate"):
        Suite.model_validate({"task": "t", "cases": [case, case]})
    bad = {**case, "checks": [{"type": "llm_judge"}]}
    with pytest.raises(ValidationError):
        Suite.model_validate({"task": "t", "cases": [bad]})


def test_defaults_run_before_case_checks(tmp_path: Path) -> None:
    path = tmp_path / "cases.yaml"
    path.write_text(
        "task: t\ndefaults: [{type: json_valid}]\n"
        "cases:\n  - {id: a, input: x, checks: [{type: max_tokens, value: 5}]}\n"
    )
    suite = load_suite(path)
    assert [c.type for c in suite.checks_for(suite.cases[0])] == ["json_valid", "max_tokens"]
