import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    timestamp = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
    agent = sa.Column(sa.String(50), nullable=False)
    event_id = sa.Column(sa.Uuid, nullable=True)
    customer_id = sa.Column(sa.Uuid, nullable=True)
    action = sa.Column(sa.String(100), nullable=False)  # classify_ticket, analyze_call, etc.
    input_summary = sa.Column(sa.Text, nullable=True)
    output_summary = sa.Column(sa.Text, nullable=True)
    confidence = sa.Column(sa.Float, nullable=True)
    human_action = sa.Column(sa.String(20), nullable=True)  # approved, edited, dismissed
    human_edit_diff = sa.Column(JSONB, nullable=True)
    dashboard_url = sa.Column(sa.String(500), nullable=True)

    __table_args__ = (
        sa.Index("idx_audit_agent", "agent"),
        sa.Index("idx_audit_timestamp", "timestamp"),
        sa.Index("idx_audit_customer", "customer_id"),
        sa.Index("idx_audit_human_action", "human_action"),
    )
