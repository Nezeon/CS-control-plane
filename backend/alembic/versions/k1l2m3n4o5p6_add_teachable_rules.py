"""Add teachable_rules table for user-taught domain knowledge

Revision ID: k1l2m3n4o5p6
Revises: j0k1l2m3n4o5
Create Date: 2026-04-01
"""
from alembic import op
import sqlalchemy as sa

revision = "k1l2m3n4o5p6"
down_revision = "j0k1l2m3n4o5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "teachable_rules",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("rule_text", sa.Text, nullable=False),
        sa.Column("customer_id", sa.Uuid, sa.ForeignKey("customers.id"), nullable=True),
        sa.Column("created_by_slack_user", sa.String(100), nullable=True),
        sa.Column("created_by_name", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_teachable_rules_customer_active", "teachable_rules", ["customer_id", "is_active"])


def downgrade() -> None:
    op.drop_index("idx_teachable_rules_customer_active", table_name="teachable_rules")
    op.drop_table("teachable_rules")
