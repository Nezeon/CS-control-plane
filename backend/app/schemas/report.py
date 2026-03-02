from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ReportListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    report_type: str
    title: str
    customer_name: str | None = None
    period_start: date | None = None
    period_end: date | None = None
    generated_at: datetime | None = None


class ReportDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    report_type: str
    title: str
    customer_name: str | None = None
    customer_id: UUID | None = None
    content: dict = {}
    period_start: date | None = None
    period_end: date | None = None
    generated_at: datetime | None = None


class GenerateReportRequest(BaseModel):
    report_type: str
    customer_id: UUID | None = None
    period_start: date | None = None
    period_end: date | None = None


class HealthHeatmap(BaseModel):
    customers: list[str]
    dates: list[str]
    scores: list[list[int | None]]


class TicketVelocity(BaseModel):
    dates: list[str]
    p1: list[int]
    p2: list[int]
    p3: list[int]
    p4: list[int]


class SentimentDistribution(BaseModel):
    dates: list[str]
    positive: list[int]
    neutral: list[int]
    negative: list[int]


class AgentPerformanceItem(BaseModel):
    name: str
    tasks: int
    success_rate: float | None = None
    avg_duration_ms: int | None = None


class AnalyticsResponse(BaseModel):
    health_heatmap: HealthHeatmap
    ticket_velocity: TicketVelocity
    sentiment_distribution: SentimentDistribution
    agent_performance: list[AgentPerformanceItem]
