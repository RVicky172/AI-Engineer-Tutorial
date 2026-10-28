"""The live regression gate: `pytest evals/` calls the real model, one test per case.

    pytest evals/                         # CURRENT prompt, 3 runs per case
    pytest evals/ --prompt-version v1     # an older or candidate version
    pytest evals/ --repeats 1 -k vpn      # quick and cheap while editing

A case passes only if every run passes every check, so a flaky case fails the gate. The report
(reports/triage-<version>.md/.json) is written at the end of the session."""

from dataclasses import dataclass, field
from pathlib import Path

import pytest
from llm_common import MessagesAPI, Settings, make_messages_api

from regression.cases import Suite, load_suite
from regression.prompts import Prompt, PromptStore
from regression.report import write_report
from regression.runner import CaseRun, SuiteRun

LAB = Path(__file__).resolve().parents[1]
SUITE = load_suite(LAB / "evals" / "cases.yaml")


@dataclass
class Session:
    api: MessagesAPI
    settings: Settings
    suite: Suite
    prompt: Prompt
    repeats: int
    effort: str
    reports: Path
    runs: list[CaseRun] = field(default_factory=list)


_session: Session | None = None


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--prompt-version", default=None, help="default: prompts/<task>/CURRENT")
    parser.addoption("--repeats", type=int, default=3)
    parser.addoption("--effort", default="low")
    parser.addoption("--reports-dir", type=Path, default=LAB / "reports")


@pytest.fixture(scope="session")
def session(request: pytest.FixtureRequest) -> Session:
    global _session
    settings = Settings.from_env()
    store = PromptStore(LAB / "prompts")
    _session = Session(
        api=make_messages_api(settings),
        settings=settings,
        suite=SUITE,
        prompt=store.load(SUITE.task, request.config.getoption("--prompt-version")),
        repeats=request.config.getoption("--repeats"),
        effort=request.config.getoption("--effort"),
        reports=request.config.getoption("--reports-dir"),
    )
    return _session


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    if _session is None or not _session.runs:
        return
    s = _session
    order = {c.id: i for i, c in enumerate(s.suite.cases)}  # -k / -x may run a subset
    runs = sorted(s.runs, key=lambda r: order[r.case.id])
    result = SuiteRun(s.suite.task, s.prompt, s.settings.api_model_id, s.effort, s.repeats, runs)
    path = write_report(result, s.reports)
    print(f"\nRegression report: {path} (${result.tally.cost_usd:.4f})")
