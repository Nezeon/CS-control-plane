from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CustomerBrief(BaseModel):
    id: UUID
    name: str


class AssigneeBrief(BaseModel):
    id: UUID
    full_name: str
    avatar_url: str | None = None


class TicketListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    jira_id: str | None = None
    customer: CustomerBrief | None = None
    summary: str
    ticket_type: str | None = None
    severity: str | None = None
    status: str | None = None
    assigned_to: AssigneeBrief | None = None
    has_triage_result: bool = False
    has_troubleshoot_result: bool = False
    sla_deadline: datetime | None = None
    sla_remaining_hours: float | None = None
    sla_breaching: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TicketDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    jira_id: str | None = None
    customer: CustomerBrief | None = None
    summary: str
    description: str | None = None
    ticket_type: str | None = None
    severity: str | None = None
    status: str | None = None
    assigned_to: AssigneeBrief | None = None
    triage_result: dict | None = None
    troubleshoot_result: dict | None = None
    escalation_summary: dict | None = None
    sla_deadline: datetime | None = None
    sla_remaining_hours: float | None = None
    sla_breaching: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None
    resolved_at: datetime | None = None


class TicketListResponse(BaseModel):
    tickets: list[TicketListItem]
    total: int
    limit: int
    offset: int


class TicketStatusUpdate(BaseModel):
    status: str


class TicketAssign(BaseModel):
    assigned_to_id: UUID
