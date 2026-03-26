"""Add is_active column to customers table

Revision ID: g7h8i9j0k1l2
Revises: f6g7h8i9j0k1
Create Date: 2026-03-25
"""
from alembic import op
import sqlalchemy as sa

revision = "g7h8i9j0k1l2"
down_revision = "f6g7h8i9j0k1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "customers",
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true"), nullable=False),
    )
    op.create_index("idx_customers_is_active", "customers", ["is_active"])


def downgrade() -> None:
    op.drop_index("idx_customers_is_active", table_name="customers")
    op.drop_column("customers", "is_active")
