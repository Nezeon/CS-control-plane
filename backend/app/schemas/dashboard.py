from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TrendData(BaseModel):
    customers_change: int = 0
    risk_change: int = 0
    tickets_change: int = 0
    health_change: float = 0.0


class DashboardStats(BaseModel):
    total_customers: int
    at_risk_count: int
    open_tickets: int
    avg_health_score: float | None
    trends: TrendData


class DashboardAgentItem(BaseModel):
    name: str
    display_name: str
    lane: str
    status: str = "idle"
    current_task: str | None = None
    tasks_today: int = 0
    avg_response_ms: int | None = None
    last_active: datetime | None = None


class DashboardEventItem(BaseModel):
    id: UUID
    event_type: str
    source: str | None = None
    description: str | None = None
    customer_name: str | None = None
    routed_to: str | None = None
    status: str | None = None
    created_at: datetime | None = None
    processed_at: datetime | None = None


class DashboardEventsResponse(BaseModel):
    events: list[DashboardEventItem]
    total: int
    limit: int
    offset: int


class QuickHealthItem(BaseModel):
    id: UUID
    name: str
    health_score: int | None = None
    risk_level: str | None = None
    risk_count: int = 0
    initial: str
