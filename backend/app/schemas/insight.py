from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.user import CsOwnerBrief


class InsightListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_id: UUID | None = None
    customer_name: str | None = None
    call_date: datetime | None = None
    participants: list = []
    summary: str | None = None
    decisions: list = []
    action_items: list = []
    risks: list = []
    sentiment: str | None = None
    sentiment_score: float | None = None
    key_topics: list[str] = []
    customer_recap_draft: str | None = None
    meeting_type: str | None = None
    highlights: list[str] = []
    conclusion: str | None = None
    processed_at: datetime | None = None


class InsightDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_id: UUID | None = None
    customer_name: str | None = None
    fathom_recording_id: str | None = None
    call_date: datetime | None = None
    participants: list = []
    summary: str | None = None
    decisions: list = []
    action_items: list = []
    risks: list = []
    sentiment: str | None = None
    sentiment_score: float | None = None
    key_topics: list[str] = []
    customer_recap_draft: str | None = None
    meeting_type: str | None = None
    highlights: list[str] = []
    conclusion: str | None = None
    raw_transcript: str | None = None
    processed_at: datetime | None = None


class InsightListResponse(BaseModel):
    insights: list[InsightListItem]
    total: int
    limit: int
    offset: int


class SentimentTrendItem(BaseModel):
    date: str
    avg_sentiment_score: float | None = None
    call_count: int = 0


class ActionItemListItem(BaseModel):
    id: UUID
    customer_name: str | None = None
    insight_id: UUID | None = None
    task: str
    owner: CsOwnerBrief | None = None
    deadline: datetime | None = None
    status: str = "pending"
    is_overdue: bool = False


class ActionItemStatusUpdate(BaseModel):
    status: str
