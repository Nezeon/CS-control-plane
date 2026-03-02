from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class HealthScoreItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    customer_id: UUID
    customer_name: str
    score: int
    risk_level: str | None = None
    risk_flags: list[str] = []
    calculated_at: datetime


class HealthScoresResponse(BaseModel):
    scores: list[HealthScoreItem]


class HealthHistoryItem(BaseModel):
    date: str
    score: int
    risk_level: str | None = None
    risk_flags: list[str] = []


class HealthHistoryResponse(BaseModel):
    customer_id: UUID
    history: list[HealthHistoryItem]


class HealthTrendItem(BaseModel):
    date: str
    avg_score: float
    at_risk_count: int


class HealthTrendsResponse(BaseModel):
    daily_averages: list[HealthTrendItem]


class RunCheckResponse(BaseModel):
    task_id: str
    message: str
    status: str
