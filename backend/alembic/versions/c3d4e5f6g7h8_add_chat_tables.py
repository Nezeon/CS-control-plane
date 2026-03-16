"""add_chat_tables

Revision ID: c3d4e5f6g7h8
Revises: a1b2c3d4e5f6
Create Date: 2026-03-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6g7h8'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- chat_conversations ---
    op.create_table('chat_conversations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('customer_id', sa.Uuid(), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='active', nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_chat_conv_user', 'chat_conversations', ['user_id', sa.text('created_at DESC')])
    op.create_index('idx_chat_conv_customer', 'chat_conversations', ['customer_id'])
    op.create_index('idx_chat_conv_status', 'chat_conversations', ['status'])

    # --- chat_messages ---
    op.create_table('chat_messages',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('conversation_id', sa.Uuid(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('event_id', sa.Uuid(), nullable=True),
        sa.Column('agents_involved', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=True),
        sa.Column('pipeline_status', sa.String(length=20), nullable=True),
        sa.Column('execution_metadata', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['chat_conversations.id']),
        sa.ForeignKeyConstraint(['event_id'], ['events.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_chat_msg_conversation', 'chat_messages', ['conversation_id', sa.text('created_at ASC')])
    op.create_index('idx_chat_msg_event', 'chat_messages', ['event_id'])


def downgrade() -> None:
    op.drop_table('chat_messages')
    op.drop_table('chat_conversations')
