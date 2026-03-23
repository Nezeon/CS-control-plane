"""Add functional index on chat_conversations metadata->>'slack_channel'

Revision ID: f6g7h8i9j0k1
Revises: e5f6g7h8i9j0
Create Date: 2026-03-23
"""
from alembic import op
import sqlalchemy as sa

revision = "f6g7h8i9j0k1"
down_revision = "e5f6g7h8i9j0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "idx_chat_conv_metadata_slack_channel",
        "chat_conversations",
        [sa.text("((metadata->>'slack_channel'))")],
        postgresql_where=sa.text("metadata->>'slack_channel' IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "idx_chat_conv_metadata_slack_channel",
        table_name="chat_conversations",
    )
