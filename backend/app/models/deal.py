"""
Deal model — HubSpot CRM deal records synced via API.

Each deal maps to a customer via company_name matching or direct customer_id FK.
"""

import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class Deal(Base):
    __tablename__ = "deals"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    hubspot_deal_id = sa.Column(sa.String(50), unique=True, nullable=False)
    deal_name = sa.Column(sa.String(500), nullable=False)
    stage = sa.Column(sa.String(100), nullable=True)
    pipeline = sa.Column(sa.String(100), nullable=True)
    amount = sa.Column(sa.Float, nullable=True)
    close_date = sa.Column(sa.Date, nullable=True)
    owner_name = sa.Column(sa.String(255), nullable=True)
    customer_id = sa.Column(sa.Uuid, sa.ForeignKey("customers.id"), nullable=True)
    company_name = sa.Column(sa.String(255), nullable=True)
    hubspot_company_id = sa.Column(sa.String(50), nullable=True)
    properties = sa.Column(JSONB, server_default=sa.text("'{}'::jsonb"))
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
    updated_at = sa.Column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()
    )
    hubspot_created_at = sa.Column(sa.DateTime(timezone=True), nullable=True)
    hubspot_updated_at = sa.Column(sa.DateTime(timezone=True), nullable=True)

    # Relationships
    customer = relationship("Customer", back_populates="deals")

    __table_args__ = (
        sa.Index("idx_deals_customer", "customer_id"),
        sa.Index("idx_deals_stage", "stage"),
        sa.Index("idx_deals_hubspot", "hubspot_deal_id"),
    )
