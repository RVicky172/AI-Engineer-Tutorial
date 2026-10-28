import pytest

from evals.conftest import SUITE, Session
from regression.cases import Case
from regression.runner import FATAL_ERRORS, Status, run_case


@pytest.mark.parametrize("case", SUITE.cases, ids=[c.id for c in SUITE.cases])
def test_case(case: Case, session: Session) -> None:
    try:
        result = run_case(
            session.api,
            session.suite,
            case,
            session.prompt,
            model=session.settings.api_model_id,
            repeats=session.repeats,
            effort=session.effort,
        )
    except FATAL_ERRORS as exc:
        # bad key, unknown model, malformed request: every case would fail the same way
        pytest.exit(f"Model call failed, stopping the suite: {exc}", returncode=2)
    session.runs.append(result)
    assert result.status is Status.PASS, f"{result.status}: {result.failure_summary}"
