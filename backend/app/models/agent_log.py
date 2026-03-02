import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    agent_name = sa.Column(sa.String(100), nullable=False)
    agent_type = sa.Column(sa.String(50), nullable=True)
    event_type = sa.Column(sa.String(100), nullable=True)
    trigger_event = sa.Column(sa.String(100), nullable=True)
    customer_id = sa.Column(sa.Uuid, sa.ForeignKey("customers.id"), nullable=True)
    input_summary = sa.Column(sa.Text, nullable=True)
    output_summary = sa.Column(sa.Text, nullable=True)
    reasoning_summary = sa.Column(sa.Text, nullable=True)
    status = sa.Column(sa.String(20), server_default="running")
    duration_ms = sa.Column(sa.Integer, nullable=True)
    metadata_ = sa.Column("metadata", JSONB, server_default=sa.text("'{}'::jsonb"))
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())

    # Relationships
    customer = relationship("Customer", back_populates="agent_logs")

    __table_args__ = (
        sa.Index("idx_agent_logs_agent_date", "agent_name", created_at.desc()),
        sa.Index("idx_agent_logs_customer", "customer_id"),
        sa.Index("idx_agent_logs_status", "status"),
    )
