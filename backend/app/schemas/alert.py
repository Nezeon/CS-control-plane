from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.user import CsOwnerBrief


class CustomerBrief(BaseModel):
    id: UUID
    name: str


class AlertListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer: CustomerBrief | None = None
    alert_type: str
    severity: str | None = None
    title: str
    description: str | None = None
    suggested_action: str | None = None
    similar_past_issues: list = []
    assigned_to: CsOwnerBrief | None = None
    status: str = "open"
    slack_notified: bool = False
    created_at: datetime | None = None


class AlertListResponse(BaseModel):
    alerts: list[AlertListItem]
    total: int
    limit: int
    offset: int
