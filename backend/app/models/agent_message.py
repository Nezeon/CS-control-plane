import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class AgentMessage(Base):
    __tablename__ = "agent_messages"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    thread_id = sa.Column(sa.Uuid, nullable=True)
    parent_id = sa.Column(sa.Uuid, sa.ForeignKey("agent_messages.id"), nullable=True)
    from_agent = sa.Column(sa.String(100), nullable=False)
    from_name = sa.Column(sa.String(255), nullable=True)
    to_agent = sa.Column(sa.String(100), nullable=False)
    to_name = sa.Column(sa.String(255), nullable=True)
    message_type = sa.Column(sa.String(50), nullable=False)
    direction = sa.Column(sa.String(20), nullable=False)
    content = sa.Column(sa.Text, nullable=False)
    priority = sa.Column(
        sa.Integer,
        sa.CheckConstraint("priority >= 1 AND priority <= 10"),
        default=5,
        server_default="5",
    )
    event_id = sa.Column(sa.Uuid, sa.ForeignKey("events.id"), nullable=True)
    execution_id = sa.Column(sa.Uuid, nullable=True)
    customer_id = sa.Column(sa.Uuid, sa.ForeignKey("customers.id"), nullable=True)
    status = sa.Column(sa.String(20), server_default="pending")
    metadata_ = sa.Column("metadata", JSONB, server_default=sa.text("'{}'::jsonb"))
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())

    # Relationships
    event = relationship("Event")
    customer = relationship("Customer")
    parent = relationship("AgentMessage", remote_side=[id])

    __table_args__ = (
        sa.Index("idx_messages_thread", "thread_id"),
        sa.Index("idx_messages_from", "from_agent", created_at.desc()),
        sa.Index("idx_messages_to", "to_agent", created_at.desc()),
        sa.Index("idx_messages_type", "message_type"),
        sa.Index("idx_messages_event", "event_id"),
        sa.Index("idx_messages_execution", "execution_id"),
        sa.Index("idx_messages_status", "status"),
    )
