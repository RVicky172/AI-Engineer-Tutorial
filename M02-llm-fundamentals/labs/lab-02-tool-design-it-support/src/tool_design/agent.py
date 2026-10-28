"""Experiment 2: a small agent loop against the fake service desk, where some calls fail on
purpose. Compares how the model recovers from terse errors vs. actionable ones."""

import json
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

import anthropic
from llm_common import MessagesAPI, UsageTally, text_of, tool_uses

from tool_design.backend import WRITE_TOOLS, ErrorStyle, FakeServiceDesk, ToolCall
from tool_design.dataset import ExpectedCall, Scenario
from tool_design.selection import FATAL_ERRORS, same_value, wrap_request
from tool_design.toolsets import SYSTEM, Version, tools_for

MAX_STEPS = 6  # model calls per scenario: a hard stop for loops


@dataclass
class RecoveryResult:
    scenario: Scenario
    style: ErrorStyle
    stop: str  # end_turn, max_steps, refusal, max_tokens, api_error
    calls: list[ToolCall] = field(default_factory=list)
    final_text: str = ""
    steps: int = 0
    tally: UsageTally = field(default_factory=lambda: UsageTally(model="unknown"))

    @property
    def errors_seen(self) -> int:
        return sum(c.outcome.is_error for c in self.calls)

    @property
    def looping(self) -> bool:
        """The same tool called too often, or the exact same call repeated after it failed."""
        per_tool = Counter(c.name for c in self.calls)
        repeats = Counter(
            (c.name, json.dumps(c.input, sort_keys=True)) for c in self.calls if c.outcome.is_error
        )
        return any(n > self.scenario.max_calls_per_tool for n in per_tool.values()) or any(
            n > 1 for n in repeats.values()
        )

    def _done(self, want: ExpectedCall) -> bool:
        return any(
            c.name == want.name
            and not c.outcome.is_error
            and all(same_value(c.input.get(k), v) for k, v in want.args.items())
            for c in self.calls
        )

    @property
    def missing(self) -> list[ExpectedCall]:
        return [want for want in self.scenario.expect if not self._done(want)]

    @property
    def success(self) -> bool:
        wrote = any(c.name in WRITE_TOOLS and not c.outcome.is_error for c in self.calls)
        return (
            self.stop == "end_turn"
            and not self.missing
            and not self.looping
            and not (self.scenario.forbid_writes and wrote)
        )


def tool_result_block(tool_use_id: str, content: str, is_error: bool) -> dict[str, Any]:
    block: dict[str, Any] = {"type": "tool_result", "tool_use_id": tool_use_id, "content": content}
    if is_error:
        block["is_error"] = True  # tells the model the call failed, so it can change course
    return block


def run_scenario(
    api: MessagesAPI,
    scenario: Scenario,
    style: ErrorStyle,
    *,
    model: str,
    effort: str = "low",
    max_tokens: int = 4096,
    max_steps: int = MAX_STEPS,
) -> RecoveryResult:
    desk = FakeServiceDesk(style=style, kb_failures=scenario.kb_failures)
    tally = UsageTally(model=model)
    messages: list[dict[str, Any]] = [{"role": "user", "content": wrap_request(scenario.request)}]
    base = {
        "model": model,
        "max_tokens": max_tokens,
        "tools": tools_for(Version.V2),  # fixed: this experiment varies only the error messages
        "system": [{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}],
        "output_config": {"effort": effort},
    }
    result = RecoveryResult(scenario, style, stop="max_steps", calls=desk.calls, tally=tally)
    for step in range(1, max_steps + 1):
        result.steps = step
        try:
            # a copy: the list keeps growing, and fakes record what was sent at this step
            reply = api.create(**base, messages=list(messages))
        except FATAL_ERRORS:
            raise
        except anthropic.APIError as exc:
            result.stop, result.final_text = "api_error", f"{type(exc).__name__}: {exc}"
            return result
        tally.add(reply.usage)
        if reply.stop_reason != "tool_use":
            result.stop = reply.stop_reason or "end_turn"
            result.final_text = text_of(reply).strip()
            return result
        # Send the assistant turn back unchanged (thinking blocks included), then ALL results in
        # ONE user message: splitting parallel results across messages teaches the model to stop
        # calling tools in parallel.
        messages.append({"role": "assistant", "content": reply.content})
        results = []
        for use in tool_uses(reply):
            outcome = desk.execute(use.name, dict(use.input))
            results.append(tool_result_block(use.id, outcome.content, outcome.is_error))
        messages.append({"role": "user", "content": results})
    return result


def run_recovery(
    api: MessagesAPI,
    scenarios: Sequence[Scenario],
    styles: Sequence[ErrorStyle],
    **kwargs: Any,
) -> list[RecoveryResult]:
    """Sequential on purpose: few scenarios, and each one is a multi-turn conversation."""
    return [run_scenario(api, s, style, **kwargs) for style in styles for s in scenarios]
