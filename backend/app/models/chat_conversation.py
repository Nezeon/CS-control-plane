import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class ChatConversation(Base):
    __tablename__ = "chat_conversations"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    user_id = sa.Column(sa.Uuid, sa.ForeignKey("users.id"), nullable=False)
    title = sa.Column(sa.String(500), nullable=True)
    customer_id = sa.Column(sa.Uuid, sa.ForeignKey("customers.id"), nullable=True)
    status = sa.Column(sa.String(20), server_default="active")
    metadata_ = sa.Column("metadata", JSONB, server_default=sa.text("'{}'::jsonb"))
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
    updated_at = sa.Column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
    )

    # Relationships
    user = relationship("User")
    customer = relationship("Customer")
    messages = relationship(
        "ChatMessage", back_populates="conversation", order_by="ChatMessage.created_at"
    )

    __table_args__ = (
        sa.Index("idx_chat_conv_user", "user_id", created_at.desc()),
        sa.Index("idx_chat_conv_customer", "customer_id"),
        sa.Index("idx_chat_conv_status", "status"),
        sa.Index(
            "idx_chat_conv_metadata_slack_channel",
            sa.text("((metadata->>'slack_channel'))"),
            postgresql_where=sa.text("metadata->>'slack_channel' IS NOT NULL"),
        ),
    )
