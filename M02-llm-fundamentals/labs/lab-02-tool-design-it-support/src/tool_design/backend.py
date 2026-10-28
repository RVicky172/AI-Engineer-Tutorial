"""An in-memory service desk that executes tool calls, so error handling can be tested end to end.

The same failure can be reported two ways. `TERSE` is what many internal APIs return; `ACTIONABLE`
says what went wrong and what to do next. The recovery experiment compares the two.
"""

import copy
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from pydantic import ValidationError

from tool_design.args import (
    ARGS,
    TOOL_NAMES,
    AddCommentArgs,
    EscalateArgs,
    GetTicketArgs,
    RestartServiceArgs,
    SearchKbArgs,
    ToolArgs,
)

WRITE_TOOLS = frozenset({"restart_service", "add_comment", "escalate"})
NUMBER_FIELDS = frozenset({"number", "ticket_number"})


class ErrorStyle(StrEnum):
    TERSE = "terse"
    ACTIONABLE = "actionable"


TICKETS: dict[str, dict[str, Any]] = {
    "INC0012345": {
        "state": "In Progress",
        "priority": "P1",
        "group": "network",
        "short_description": "VPN gateway unreachable for the Pune office",
        "comments": ["Gateway vpn-gw-02 failing health checks"],
    },
    "INC0012346": {
        "state": "New",
        "priority": "P3",
        "group": "end-user-computing",
        "requester": "grace.liu@acme.example",
        "short_description": "Laptop does not boot",
        "comments": [],
    },
    "INC0012347": {
        "state": "In Progress",
        "priority": "P2",
        "group": "service-desk",
        "short_description": "ERP invoice posting fails with timeout",
        "comments": ["Started after last night's ERP release"],
    },
    "INC0012348": {
        "state": "New",
        "priority": "P1",
        "group": "service-desk",
        "short_description": "User entered credentials on a phishing page",
        "comments": [],
    },
    "INC0012349": {
        "state": "Closed",
        "priority": "P4",
        "group": "end-user-computing",
        "short_description": "Printer on floor 3 jams",
        "comments": ["Toner replaced"],
    },
    "INC0012350": {
        "state": "In Progress",
        "priority": "P2",
        "group": "service-desk",
        "short_description": "Outbound mail queue stuck on mail relay",
        "comments": ["Queue at 4,000 messages"],
    },
    "INC0012351": {
        "state": "New",
        "priority": "P1",
        "group": "identity",
        "short_description": "SSO login page returns 503 for all users",
        "comments": [],
    },
}

KB: list[dict[str, str]] = [
    {
        "id": "KB0001",
        "title": "Reset your SSO password or re-enrol MFA on a new phone",
        "keywords": "sso password reset locked mfa authenticator phone enrol enroll",
        "fix": "Use https://id.acme.example/reset, then scan the new QR code in the app.",
    },
    {
        "id": "KB0002",
        "title": "VPN client shows 'gateway unreachable'",
        "keywords": "vpn gateway unreachable client connect tunnel",
        "fix": "Switch to the backup gateway vpn-gw-01 in the client settings.",
    },
    {
        "id": "KB0003",
        "title": "Restart the print spooler on your Windows laptop",
        "keywords": "print spooler printer stuck queue windows laptop",
        "fix": "Run services.msc, right-click Print Spooler and choose Restart.",
    },
    {
        "id": "KB0004",
        "title": "Outlook on iPhone or Android stops syncing",
        "keywords": "outlook mobile iphone android phone sync mail email",
        "fix": "Remove the account in the Outlook app and add it again.",
    },
    {
        "id": "KB0005",
        "title": "ERP invoice posting fails with timeout",
        "keywords": "erp invoice posting timeout fails error",
        "fix": "Known issue after release 24.3; ERP support is rolling back.",
    },
    {
        "id": "KB0006",
        "title": "Report a phishing email",
        "keywords": "phishing suspicious email report clicked link",
        "fix": "Use the Report Phishing button; if you entered a password, call security.",
    },
]

# service -> (why it is frozen, the group that owns it)
FROZEN: dict[str, tuple[str, str]] = {
    "erp-app": (
        "change CHG0004321 (ERP release rollback) freezes erp-app until 18:00 UTC",
        "erp-support",
    ),
}


@dataclass(frozen=True)
class ToolOutcome:
    content: str
    is_error: bool = False


@dataclass(frozen=True)
class ToolCall:
    name: str
    input: dict[str, Any]
    outcome: ToolOutcome


def _compact(data: object) -> str:
    """Tool results go back into the context window: no indentation, only the fields needed."""
    return json.dumps(data, separators=(",", ":"))


@dataclass
class FakeServiceDesk:
    style: ErrorStyle = ErrorStyle.ACTIONABLE
    kb_failures: int = 0  # the first N searches time out, to test recovery from transient errors
    tickets: dict[str, dict[str, Any]] = field(default_factory=lambda: copy.deepcopy(TICKETS))
    calls: list[ToolCall] = field(default_factory=list)

    @property
    def writes(self) -> list[ToolCall]:
        """Calls that changed something. Failed writes changed nothing, so they don't count."""
        return [c for c in self.calls if c.name in WRITE_TOOLS and not c.outcome.is_error]

    def execute(self, name: str, tool_input: Mapping[str, Any]) -> ToolOutcome:
        outcome = self._dispatch(name, tool_input)
        self.calls.append(ToolCall(name, dict(tool_input), outcome))
        return outcome

    def _error(self, terse: str, actionable: str) -> ToolOutcome:
        return ToolOutcome(terse if self.style is ErrorStyle.TERSE else actionable, is_error=True)

    def _dispatch(self, name: str, tool_input: Mapping[str, Any]) -> ToolOutcome:
        model = ARGS.get(name)
        if model is None:
            return self._error(
                "Error: unknown tool", f"There is no tool named {name!r}. Tools: {TOOL_NAMES}."
            )
        try:
            args = model.model_validate(tool_input)
        except ValidationError as exc:
            return self._error("Error 400: invalid input", self._explain(name, exc, tool_input))
        return self._run(args)

    def _run(self, args: ToolArgs) -> ToolOutcome:
        if isinstance(args, GetTicketArgs):
            return self._get_ticket(args)
        if isinstance(args, SearchKbArgs):
            return self._search_kb(args)
        if isinstance(args, RestartServiceArgs):
            return self._restart_service(args)
        if isinstance(args, AddCommentArgs):
            return self._add_comment(args)
        if isinstance(args, EscalateArgs):
            return self._escalate(args)
        raise TypeError(f"no handler for {type(args).__name__}")  # pragma: no cover

    def _explain(self, name: str, exc: ValidationError, tool_input: Mapping[str, Any]) -> str:
        problems = "; ".join(
            f"{'.'.join(str(p) for p in e['loc']) or '<input>'}: {e['msg']}" for e in exc.errors()
        )
        message = f"Invalid arguments for {name}: {problems}."
        bad_fields = {str(e["loc"][0]) for e in exc.errors() if e["loc"]}
        for key in NUMBER_FIELDS & bad_fields:
            message += " Incident numbers are INC followed by exactly 7 digits, e.g. INC0012345."
            if suggestion := self._did_you_mean(str(tool_input.get(key, ""))):
                message += f" Did you mean {suggestion}?"
        return message

    def _did_you_mean(self, raw: str) -> str | None:
        """'inc12346' -> 'INC0012346', but only if that incident exists. Never guess further."""
        digits = re.fullmatch(r"(?i)\s*inc\s*0*(\d{1,7})\s*", raw)
        if not digits:
            return None
        candidate = f"INC{int(digits.group(1)):07d}"
        return candidate if candidate in self.tickets else None

    def _ticket_or_error(self, number: str) -> dict[str, Any] | ToolOutcome:
        ticket = self.tickets.get(number)
        if ticket is None:
            return self._error(
                "Error 404",
                f"No incident {number} exists. Ask the user to confirm the number; "
                "do not guess another one.",
            )
        return ticket

    def _get_ticket(self, args: GetTicketArgs) -> ToolOutcome:
        ticket = self._ticket_or_error(args.number)
        if isinstance(ticket, ToolOutcome):
            return ticket
        return ToolOutcome(
            _compact({"number": args.number, **ticket, "comments": ticket["comments"][-3:]})
        )

    def _search_kb(self, args: SearchKbArgs) -> ToolOutcome:
        if self.kb_failures > 0:
            self.kb_failures -= 1
            return self._error(
                "Error 504",
                "The knowledge base timed out (temporary). Retry the same search once; if it "
                "fails again, tell the user search is unavailable.",
            )
        words = set(re.findall(r"[a-z0-9]+", args.query.lower()))
        scored = [
            (len(words & set(f"{a['title']} {a['keywords']}".lower().split())), a) for a in KB
        ]
        hits = [
            {k: a[k] for k in ("id", "title", "fix")}
            for score, a in sorted(scored, key=lambda s: -s[0])
            if score > 0
        ][:3]
        if not hits:
            return ToolOutcome(_compact({"results": [], "hint": "Try fewer, broader keywords."}))
        return ToolOutcome(_compact({"results": hits}))

    def _restart_service(self, args: RestartServiceArgs) -> ToolOutcome:
        ticket = self._ticket_or_error(args.ticket_number)
        if isinstance(ticket, ToolOutcome):
            return ticket
        if args.service in FROZEN:
            why, owner = FROZEN[args.service]
            return self._error(
                "Error 409",
                f"Restart blocked: {why}. Do not retry. Escalate {args.ticket_number} to the "
                f"owning group instead (escalate with group={owner}).",
            )
        return ToolOutcome(_compact({"service": args.service, "status": "running", "restarted": 1}))

    def _add_comment(self, args: AddCommentArgs) -> ToolOutcome:
        ticket = self._ticket_or_error(args.ticket_number)
        if isinstance(ticket, ToolOutcome):
            return ticket
        if ticket["state"] == "Closed":
            return self._error(
                "Error 409",
                f"{args.ticket_number} is Closed and accepts no comments. Do not retry. Tell "
                "the user and ask whether they want a new incident opened.",
            )
        ticket["comments"].append(args.text)
        return ToolOutcome(_compact({"comment_id": f"C{len(ticket['comments']):03d}"}))

    def _escalate(self, args: EscalateArgs) -> ToolOutcome:
        ticket = self._ticket_or_error(args.ticket_number)
        if isinstance(ticket, ToolOutcome):
            return ticket
        ticket["group"] = args.group
        return ToolOutcome(_compact({"number": args.ticket_number, "group": args.group}))
