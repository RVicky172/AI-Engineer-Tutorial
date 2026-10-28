from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from regression.checks import Check


class Case(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[a-z0-9-]+$")  # also the pytest test id
    input: str
    tags: list[str] = Field(default_factory=list)
    checks: list[Check] = Field(min_length=1)


class Suite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task: str
    defaults: list[Check] = Field(
        default_factory=list, description="Checks applied to every case, before its own"
    )
    cases: list[Case]

    @model_validator(mode="after")
    def unique_ids(self) -> "Suite":
        ids = [c.id for c in self.cases]
        if dupes := sorted({i for i in ids if ids.count(i) > 1}):
            raise ValueError(f"duplicate case ids: {dupes}")
        return self

    def checks_for(self, case: Case) -> list[Check]:
        return [*self.defaults, *case.checks]


def load_suite(path: Path) -> Suite:
    return Suite.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
