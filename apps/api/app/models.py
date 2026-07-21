from datetime import UTC, datetime
from enum import StrEnum
from pydantic import BaseModel, Field


class Role(StrEnum):
    admin = "Admin"
    technician = "Technician"
    readonly = "ReadOnly"


class AuditAction(StrEnum):
    login = "login"
    search = "search"
    assistant_answer = "assistant_answer"
    feedback = "feedback"
    admin_action = "admin_action"
    authorization_denied = "authorization_denied"
    verifier_failed = "verifier_failed"


class AuditLogEntry(BaseModel):
    actor: str
    action: AuditAction
    target: str | None = None
    outcome: str = "success"
    scope: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class LoginRequest(BaseModel):
    username: str
    password: str


class AnswerFormat(BaseModel):
    confidence: float = Field(ge=0, le=1)
    related_tickets: list[str] = Field(default_factory=list)
    from_compuone_ticket_history: str
    general_it_guidance: str
    suggested_next_steps: list[str]
    based_on_tickets: list[str]


REQUIRED_ANSWER_SECTIONS = (
    "From CompuOne Ticket History",
    "General IT Guidance",
    "Suggested Next Steps",
    "Based on Tickets",
    "Warnings",
)
