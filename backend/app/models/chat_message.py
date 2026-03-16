import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    conversation_id = sa.Column(
        sa.Uuid, sa.ForeignKey("chat_conversations.id"), nullable=False
    )
    role = sa.Column(sa.String(20), nullable=False)  # user | assistant | system
    content = sa.Column(sa.Text, nullable=False)
    event_id = sa.Column(sa.Uuid, sa.ForeignKey("events.id"), nullable=True)
    agents_involved = sa.Column(JSONB, server_default=sa.text("'[]'::jsonb"))
    pipeline_status = sa.Column(sa.String(20), nullable=True)  # processing | completed | failed
    execution_metadata = sa.Column(JSONB, server_default=sa.text("'{}'::jsonb"))
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())

    # Relationships
    conversation = relationship("ChatConversation", back_populates="messages")
    event = relationship("Event")

    __table_args__ = (
        sa.Index("idx_chat_msg_conversation", "conversation_id", created_at.asc()),
        sa.Index("idx_chat_msg_event", "event_id"),
    )
