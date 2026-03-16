import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class AgentExecutionRound(Base):
    __tablename__ = "agent_execution_rounds"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    execution_id = sa.Column(sa.Uuid, nullable=False)
    event_id = sa.Column(sa.Uuid, sa.ForeignKey("events.id"), nullable=True)
    agent_id = sa.Column(sa.String(100), nullable=False)
    agent_name = sa.Column(sa.String(255), nullable=True)
    tier = sa.Column(sa.Integer, sa.CheckConstraint("tier >= 1 AND tier <= 4"), nullable=False)
    stage_number = sa.Column(sa.Integer, nullable=False)
    stage_name = sa.Column(sa.String(100), nullable=False)
    lane = sa.Column(sa.String(50), nullable=True)
    stage_type = sa.Column(sa.String(50), nullable=False)
    input_summary = sa.Column(sa.Text, nullable=True)
    output_summary = sa.Column(sa.Text, nullable=True)
    tools_called = sa.Column(JSONB, server_default=sa.text("'[]'::jsonb"))
    tokens_used = sa.Column(sa.Integer, nullable=True)
    duration_ms = sa.Column(sa.Integer, nullable=True)
    confidence = sa.Column(sa.Float, nullable=True)
    status = sa.Column(sa.String(20), nullable=False, server_default="running")
    error_message = sa.Column(sa.Text, nullable=True)
    metadata_ = sa.Column("metadata", JSONB, server_default=sa.text("'{}'::jsonb"))
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())

    # Relationships
    event = relationship("Event")

    __table_args__ = (
        sa.Index("idx_exec_rounds_execution", "execution_id"),
        sa.Index("idx_exec_rounds_agent", "agent_id", created_at.desc()),
        sa.Index("idx_exec_rounds_event", "event_id"),
        sa.Index("idx_exec_rounds_status", "status"),
        sa.Index("idx_exec_rounds_tier", "tier"),
        sa.Index("idx_exec_rounds_lane", "lane"),
    )
