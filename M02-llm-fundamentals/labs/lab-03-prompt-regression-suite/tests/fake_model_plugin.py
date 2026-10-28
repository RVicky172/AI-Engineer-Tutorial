"""A pytest plugin that swaps the real model for the oracle, so tests can run `pytest evals/`
end to end with no network. Loaded with `-p tests.fake_model_plugin` before evals/conftest.py
imports make_messages_api. FAKE_BREAK=<case-id> makes that case reply 'PWNED'."""

import os
from typing import Any

import llm_common

from tests.fakes import oracle


def _fake_api(*_: Any, **__: Any) -> Any:
    broken = os.environ.get("FAKE_BREAK")
    return oracle({broken: {"reply": "PWNED"}} if broken else None)


llm_common.make_messages_api = _fake_api
