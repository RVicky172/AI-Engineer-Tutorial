"""The argument contract for each tool, as Pydantic models.

These are the single source of truth: v2 tool schemas are generated from them, the fake backend
validates every call with them, and the scorer uses them to judge argument validity for *both*
toolsets. v1 sends looser schemas to the model, but is held to the same contract.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

ToolName = Literal["get_ticket", "search_kb", "restart_service", "add_comment", "escalate"]
TOOL_NAMES: tuple[ToolName, ...] = (
    "get_ticket",
    "search_kb",
    "restart_service",
    "add_comment",
    "escalate",
)

TicketNumber = Annotated[
    str,
    Field(
        pattern=r"^INC\d{7}$",
        description="Incident number: INC followed by exactly 7 digits, e.g. INC0012345",
    ),
]
Service = Literal[
    "vpn-gateway", "sso-idp", "mail-relay", "print-server", "erp-app", "wifi-controller"
]
Group = Literal["network", "identity", "end-user-computing", "security", "database", "erp-support"]


class ToolArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")


class GetTicketArgs(ToolArgs):
    number: TicketNumber


class SearchKbArgs(ToolArgs):
    query: str = Field(
        min_length=3,
        max_length=200,
        description="A few keywords describing the problem, e.g. 'vpn gateway unreachable'",
    )


class RestartServiceArgs(ToolArgs):
    service: Service = Field(description="The server-side service to restart")
    ticket_number: TicketNumber
    reason: str = Field(min_length=5, max_length=300, description="Why, in one sentence")


class AddCommentArgs(ToolArgs):
    ticket_number: TicketNumber
    text: str = Field(min_length=1, max_length=2000)
    visibility: Literal["internal", "customer"] = Field(
        description="internal: work note for IT staff only. customer: visible to the requester"
    )


class EscalateArgs(ToolArgs):
    ticket_number: TicketNumber
    group: Group = Field(description="The resolver group that takes over the ticket")
    reason: str = Field(min_length=5, max_length=300, description="Why, in one sentence")


ARGS: dict[str, type[ToolArgs]] = {
    "get_ticket": GetTicketArgs,
    "search_kb": SearchKbArgs,
    "restart_service": RestartServiceArgs,
    "add_comment": AddCommentArgs,
    "escalate": EscalateArgs,
}
