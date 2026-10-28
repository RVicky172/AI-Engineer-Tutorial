from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Service = Literal[
    "email",
    "vpn",
    "sso",
    "device",
    "wifi",
    "printer",
    "erp",
    "crm",
    "database",
    "security",
    "other",
]
Severity = Literal["P1", "P2", "P3", "P4"]


class Ticket(BaseModel):
    """The single source of truth for the output: the structured-output schema and the
    validator both come from this class. The prompt's field list is written by hand, so a test
    checks it names every allowed value."""

    model_config = ConfigDict(extra="forbid")

    service: Service
    severity: Severity
    requester: str = Field(
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
        description="Email address of the person who needs help",
    )
    summary: str = Field(min_length=1, max_length=200, description="One English sentence")

    @field_validator("requester")
    @classmethod
    def lowercase(cls, value: str) -> str:
        return value.lower()


class LabelledEmail(BaseModel):
    id: str
    email: str
    expected: Ticket
