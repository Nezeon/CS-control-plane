from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EventCreate(BaseModel):
    event_type: str
    source: str | None = None
    payload: dict = {}
    customer_id: UUID | None = None


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_type: str
    status: str | None = None
    created_at: datetime | None = None


class EventListItem(BaseModel):
    id: UUID
    event_type: str
    source: str | None = None
    payload: dict = {}
    status: str | None = None
    routed_to: str | None = None
    customer_id: UUID | None = None
    customer_name: str | None = None
    created_at: datetime | None = None
    processed_at: datetime | None = None


class EventListResponse(BaseModel):
    events: list[EventListItem]
    total: int
    limit: int
    offset: int
