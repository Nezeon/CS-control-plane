import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


class AgentDraft(Base):
    __tablename__ = "agent_drafts"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    agent_id = sa.Column(sa.String(50), nullable=False)
    event_id = sa.Column(sa.Uuid, sa.ForeignKey("events.id", ondelete="SET NULL"), nullable=True)
    customer_id = sa.Column(sa.Uuid, sa.ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    draft_type = sa.Column(sa.String(50), nullable=False)  # triage, call_intel, escalation, health_alert, etc.
    draft_content = sa.Column(JSONB, nullable=False)  # Full agent output
    status = sa.Column(sa.String(20), server_default="pending")  # pending, approved, edited, dismissed
    slack_message_ts = sa.Column(sa.String(50), nullable=True)  # Slack ts for updating message
    slack_channel = sa.Column(sa.String(100), nullable=True)
    approved_by = sa.Column(sa.String(100), nullable=True)
    approved_at = sa.Column(sa.DateTime(timezone=True), nullable=True)
    edit_diff = sa.Column(JSONB, nullable=True)  # What the human changed
    confidence = sa.Column(sa.Float, nullable=True)
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())

    __table_args__ = (
        sa.Index("idx_drafts_status", "status"),
        sa.Index("idx_drafts_agent", "agent_id"),
        sa.Index("idx_drafts_customer", "customer_id"),
        sa.Index("idx_drafts_created", "created_at"),
    )
