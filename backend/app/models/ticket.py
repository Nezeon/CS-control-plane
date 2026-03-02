import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    jira_id = sa.Column(sa.String(50), unique=True, nullable=True)
    customer_id = sa.Column(sa.Uuid, sa.ForeignKey("customers.id"), nullable=True)
    summary = sa.Column(sa.Text, nullable=False)
    description = sa.Column(sa.Text, nullable=True)
    ticket_type = sa.Column(sa.String(50), nullable=True)
    severity = sa.Column(sa.String(10), nullable=True)
    status = sa.Column(sa.String(50), nullable=True)
    assigned_to_id = sa.Column(sa.Uuid, sa.ForeignKey("users.id"), nullable=True)
    triage_result = sa.Column(JSONB, nullable=True)
    troubleshoot_result = sa.Column(JSONB, nullable=True)
    escalation_summary = sa.Column(JSONB, nullable=True)
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
    updated_at = sa.Column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()
    )
    resolved_at = sa.Column(sa.DateTime(timezone=True), nullable=True)
    sla_deadline = sa.Column(sa.DateTime(timezone=True), nullable=True)

    # Relationships
    customer = relationship("Customer", back_populates="tickets")
    assigned_to = relationship("User", back_populates="assigned_tickets", foreign_keys=[assigned_to_id])

    __table_args__ = (
        sa.Index("idx_tickets_customer", "customer_id"),
        sa.Index("idx_tickets_status", "status"),
        sa.Index("idx_tickets_severity", "severity"),
        sa.Index("idx_tickets_jira", "jira_id"),
        sa.Index("idx_tickets_assigned", "assigned_to_id"),
        sa.Index(
            "idx_tickets_sla",
            "sla_deadline",
            postgresql_where=sa.text("status NOT IN ('resolved', 'closed')"),
        ),
    )
