from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    thread_id: UUID | None = None
    parent_id: UUID | None = None
    from_agent: str
    from_name: str | None = None
    to_agent: str
    to_name: str | None = None
    message_type: str
    direction: str
    content: str
    priority: int = 5
    event_id: UUID | None = None
    customer_name: str | None = None
    status: str | None = None
    created_at: datetime | None = None
    reply_count: int = 0


class MessageThreadResponse(BaseModel):
    thread_id: UUID
    event_id: UUID | None = None
    customer_name: str | None = None
    messages: list[MessageResponse]
    total_messages: int


class MessageListResponse(BaseModel):
    messages: list[MessageResponse]
    total: int
    limit: int
    offset: int
