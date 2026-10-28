from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from tool_design.args import ToolName

Category = Literal["clear", "ambiguous", "no_tool", "parallel"]


class _Record(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Case(_Record):
    """One labelled request for the selection experiment."""

    id: str
    request: str
    category: Category
    expected_tools: list[ToolName] = Field(description="[] means: answer or ask, call nothing")
    also_ok: list[list[ToolName]] = Field(
        default_factory=list,
        description="Other tool sets a careful engineer would accept. Use sparingly: every "
        "alternative makes the metric easier to pass.",
    )
    expected_args: dict[ToolName, dict[str, str]] = Field(default_factory=dict)
    why: str = Field(description="Why this label is right; if you can't write it, relabel")


class ExpectedCall(_Record):
    name: ToolName
    args: dict[str, str] = Field(default_factory=dict)


class Scenario(_Record):
    """One request for the error-recovery experiment, where some tool calls fail on purpose."""

    id: str
    request: str
    kb_failures: int = 0
    expect: list[ExpectedCall] = Field(
        default_factory=list, description="Successful calls that must happen"
    )
    forbid_writes: bool = False
    max_calls_per_tool: int = 3  # more than this counts as looping
    why: str


def load_jsonl[R: _Record](path: Path, model: type[R]) -> list[R]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [model.model_validate_json(line) for line in lines if line.strip()]
