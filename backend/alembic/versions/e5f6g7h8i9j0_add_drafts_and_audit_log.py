"""Add agent_drafts and audit_log tables

Revision ID: e5f6g7h8i9j0
Revises: d4e5f6g7h8i9
Create Date: 2026-03-16
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "e5f6g7h8i9j0"
down_revision = "d4e5f6g7h8i9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # agent_drafts table
    op.create_table(
        "agent_drafts",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("agent_id", sa.String(50), nullable=False),
        sa.Column("event_id", sa.Uuid, sa.ForeignKey("events.id", ondelete="SET NULL"), nullable=True),
        sa.Column("customer_id", sa.Uuid, sa.ForeignKey("customers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("draft_type", sa.String(50), nullable=False),
        sa.Column("draft_content", JSONB, nullable=False),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("slack_message_ts", sa.String(50), nullable=True),
        sa.Column("slack_channel", sa.String(100), nullable=True),
        sa.Column("approved_by", sa.String(100), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("edit_diff", JSONB, nullable=True),
        sa.Column("confidence", sa.Float, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_drafts_status", "agent_drafts", ["status"])
    op.create_index("idx_drafts_agent", "agent_drafts", ["agent_id"])
    op.create_index("idx_drafts_customer", "agent_drafts", ["customer_id"])
    op.create_index("idx_drafts_created", "agent_drafts", ["created_at"])

    # audit_log table
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("agent", sa.String(50), nullable=False),
        sa.Column("event_id", sa.Uuid, nullable=True),
        sa.Column("customer_id", sa.Uuid, nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("input_summary", sa.Text, nullable=True),
        sa.Column("output_summary", sa.Text, nullable=True),
        sa.Column("confidence", sa.Float, nullable=True),
        sa.Column("human_action", sa.String(20), nullable=True),
        sa.Column("human_edit_diff", JSONB, nullable=True),
        sa.Column("dashboard_url", sa.String(500), nullable=True),
    )
    op.create_index("idx_audit_agent", "audit_log", ["agent"])
    op.create_index("idx_audit_timestamp", "audit_log", ["timestamp"])
    op.create_index("idx_audit_customer", "audit_log", ["customer_id"])
    op.create_index("idx_audit_human_action", "audit_log", ["human_action"])


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("agent_drafts")
