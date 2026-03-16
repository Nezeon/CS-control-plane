from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ChatSendRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    customer_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None


class ChatSendResponse(BaseModel):
    conversation_id: UUID
    message_id: UUID
    event_id: Optional[UUID] = None
    status: str  # "processing" | "completed"


class ChatMessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    event_id: Optional[UUID] = None
    agents_involved: list[str] = []
    pipeline_status: Optional[str] = None
    execution_metadata: dict = {}
    created_at: datetime

    class Config:
        from_attributes = True


class ChatConversationSummary(BaseModel):
    id: UUID
    title: Optional[str] = None
    customer_id: Optional[UUID] = None
    customer_name: Optional[str] = None
    message_count: int = 0
    last_message_at: Optional[datetime] = None
    status: str
    created_at: datetime


class ChatConversationListResponse(BaseModel):
    conversations: list[ChatConversationSummary]
    total: int


class ChatConversationDetailResponse(BaseModel):
    id: UUID
    title: Optional[str] = None
    customer_id: Optional[UUID] = None
    customer_name: Optional[str] = None
    status: str
    messages: list[ChatMessageResponse]
    created_at: datetime
