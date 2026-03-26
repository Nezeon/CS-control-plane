"""Add deals table for HubSpot CRM integration

Revision ID: h8i9j0k1l2m3
Revises: g7h8i9j0k1l2
Create Date: 2026-03-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "h8i9j0k1l2m3"
down_revision = "g7h8i9j0k1l2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "deals",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("hubspot_deal_id", sa.String(50), unique=True, nullable=False),
        sa.Column("deal_name", sa.String(500), nullable=False),
        sa.Column("stage", sa.String(100), nullable=True),
        sa.Column("pipeline", sa.String(100), nullable=True),
        sa.Column("amount", sa.Float, nullable=True),
        sa.Column("close_date", sa.Date, nullable=True),
        sa.Column("owner_name", sa.String(255), nullable=True),
        sa.Column("customer_id", sa.Uuid, sa.ForeignKey("customers.id"), nullable=True),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("hubspot_company_id", sa.String(50), nullable=True),
        sa.Column("properties", JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("hubspot_created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("hubspot_updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_deals_customer", "deals", ["customer_id"])
    op.create_index("idx_deals_stage", "deals", ["stage"])
    op.create_index("idx_deals_hubspot", "deals", ["hubspot_deal_id"])


def downgrade() -> None:
    op.drop_index("idx_deals_hubspot", table_name="deals")
    op.drop_index("idx_deals_stage", table_name="deals")
    op.drop_index("idx_deals_customer", table_name="deals")
    op.drop_table("deals")
