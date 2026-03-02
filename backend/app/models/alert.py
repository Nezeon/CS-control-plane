import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    customer_id = sa.Column(
        sa.Uuid, sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False
    )
    alert_type = sa.Column(sa.String(50), nullable=False)
    severity = sa.Column(sa.String(20), nullable=True)
    title = sa.Column(sa.Text, nullable=False)
    description = sa.Column(sa.Text, nullable=True)
    suggested_action = sa.Column(sa.Text, nullable=True)
    similar_past_issues = sa.Column(JSONB, server_default=sa.text("'[]'::jsonb"))
    assigned_to_id = sa.Column(sa.Uuid, sa.ForeignKey("users.id"), nullable=True)
    status = sa.Column(sa.String(20), server_default="open")
    slack_notified = sa.Column(sa.Boolean, server_default=sa.text("false"))
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
    resolved_at = sa.Column(sa.DateTime(timezone=True), nullable=True)

    # Relationships
    customer = relationship("Customer", back_populates="alerts")
    assigned_to = relationship("User", back_populates="assigned_alerts", foreign_keys=[assigned_to_id])

    __table_args__ = (
        sa.Index("idx_alerts_customer", "customer_id"),
        sa.Index("idx_alerts_status", "status"),
        sa.Index("idx_alerts_severity", "severity"),
    )
