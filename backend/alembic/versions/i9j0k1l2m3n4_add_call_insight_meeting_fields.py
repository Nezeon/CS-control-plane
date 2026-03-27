"""Add meeting_type, highlights, conclusion to call_insights

Revision ID: i9j0k1l2m3n4
Revises: h8i9j0k1l2m3
Create Date: 2026-03-27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "i9j0k1l2m3n4"
down_revision = "h8i9j0k1l2m3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("call_insights", sa.Column("meeting_type", sa.String(30), nullable=True, server_default=sa.text("'Other'")))
    op.add_column("call_insights", sa.Column("highlights", JSONB, server_default=sa.text("'[]'::jsonb")))
    op.add_column("call_insights", sa.Column("conclusion", sa.Text, nullable=True))


def downgrade() -> None:
    op.drop_column("call_insights", "conclusion")
    op.drop_column("call_insights", "highlights")
    op.drop_column("call_insights", "meeting_type")
