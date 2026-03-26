import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    name = sa.Column(sa.String(255), nullable=False)
    industry = sa.Column(sa.String(100), nullable=True)
    tier = sa.Column(sa.String(50), nullable=True)
    contract_start = sa.Column(sa.Date, nullable=True)
    renewal_date = sa.Column(sa.Date, nullable=True)
    primary_contact_name = sa.Column(sa.String(255), nullable=True)
    primary_contact_email = sa.Column(sa.String(255), nullable=True)
    cs_owner_id = sa.Column(sa.Uuid, sa.ForeignKey("users.id"), nullable=True)
    jira_project_key = sa.Column(sa.String(20), nullable=True)  # e.g. "CS", "ACME"
    is_active = sa.Column(sa.Boolean, server_default=sa.text("true"), nullable=False)
    deployment_mode = sa.Column(sa.String(50), server_default="OVA")
    product_version = sa.Column(sa.String(50), nullable=True)
    integrations = sa.Column(JSONB, server_default=sa.text("'[]'::jsonb"))
    known_constraints = sa.Column(JSONB, server_default=sa.text("'[]'::jsonb"))
    metadata_ = sa.Column("metadata", JSONB, server_default=sa.text("'{}'::jsonb"))
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
    updated_at = sa.Column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()
    )

    # Relationships
    cs_owner = relationship("User", back_populates="owned_customers", foreign_keys=[cs_owner_id])
    health_scores = relationship("HealthScore", back_populates="customer", cascade="all, delete-orphan")
    tickets = relationship("Ticket", back_populates="customer")
    call_insights = relationship("CallInsight", back_populates="customer")
    agent_logs = relationship("AgentLog", back_populates="customer")
    events = relationship("Event", back_populates="customer")
    alerts = relationship("Alert", back_populates="customer", cascade="all, delete-orphan")
    action_items = relationship("ActionItem", back_populates="customer")
    reports = relationship("Report", back_populates="customer")

    __table_args__ = (
        sa.Index("idx_customers_cs_owner", "cs_owner_id"),
        sa.Index("idx_customers_tier", "tier"),
        sa.Index("idx_customers_renewal", "renewal_date"),
        sa.Index("idx_customers_is_active", "is_active"),
    )
