"""add_agent_execution_rounds_and_messages

Revision ID: a1b2c3d4e5f6
Revises: 72e7ed43351d
Create Date: 2026-03-02 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '72e7ed43351d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- agent_execution_rounds ---
    op.create_table('agent_execution_rounds',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('execution_id', sa.Uuid(), nullable=False),
        sa.Column('event_id', sa.Uuid(), nullable=True),
        sa.Column('agent_id', sa.String(length=100), nullable=False),
        sa.Column('agent_name', sa.String(length=255), nullable=True),
        sa.Column('tier', sa.Integer(), nullable=False),
        sa.Column('stage_number', sa.Integer(), nullable=False),
        sa.Column('stage_name', sa.String(length=100), nullable=False),
        sa.Column('lane', sa.String(length=50), nullable=True),
        sa.Column('stage_type', sa.String(length=50), nullable=False),
        sa.Column('input_summary', sa.Text(), nullable=True),
        sa.Column('output_summary', sa.Text(), nullable=True),
        sa.Column('tools_called', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='running', nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.CheckConstraint('tier >= 1 AND tier <= 4', name='ck_exec_rounds_tier'),
        sa.ForeignKeyConstraint(['event_id'], ['events.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_exec_rounds_execution', 'agent_execution_rounds', ['execution_id'])
    op.create_index('idx_exec_rounds_agent', 'agent_execution_rounds', ['agent_id', sa.text('created_at DESC')])
    op.create_index('idx_exec_rounds_event', 'agent_execution_rounds', ['event_id'])
    op.create_index('idx_exec_rounds_status', 'agent_execution_rounds', ['status'])
    op.create_index('idx_exec_rounds_tier', 'agent_execution_rounds', ['tier'])
    op.create_index('idx_exec_rounds_lane', 'agent_execution_rounds', ['lane'])

    # --- agent_messages ---
    op.create_table('agent_messages',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('thread_id', sa.Uuid(), nullable=True),
        sa.Column('parent_id', sa.Uuid(), nullable=True),
        sa.Column('from_agent', sa.String(length=100), nullable=False),
        sa.Column('from_name', sa.String(length=255), nullable=True),
        sa.Column('to_agent', sa.String(length=100), nullable=False),
        sa.Column('to_name', sa.String(length=255), nullable=True),
        sa.Column('message_type', sa.String(length=50), nullable=False),
        sa.Column('direction', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('priority', sa.Integer(), server_default='5', nullable=True),
        sa.Column('event_id', sa.Uuid(), nullable=True),
        sa.Column('execution_id', sa.Uuid(), nullable=True),
        sa.Column('customer_id', sa.Uuid(), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='pending', nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.CheckConstraint('priority >= 1 AND priority <= 10', name='ck_messages_priority'),
        sa.ForeignKeyConstraint(['event_id'], ['events.id']),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id']),
        sa.ForeignKeyConstraint(['parent_id'], ['agent_messages.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_messages_thread', 'agent_messages', ['thread_id'])
    op.create_index('idx_messages_from', 'agent_messages', ['from_agent', sa.text('created_at DESC')])
    op.create_index('idx_messages_to', 'agent_messages', ['to_agent', sa.text('created_at DESC')])
    op.create_index('idx_messages_type', 'agent_messages', ['message_type'])
    op.create_index('idx_messages_event', 'agent_messages', ['event_id'])
    op.create_index('idx_messages_execution', 'agent_messages', ['execution_id'])
    op.create_index('idx_messages_status', 'agent_messages', ['status'])


def downgrade() -> None:
    op.drop_table('agent_messages')
    op.drop_table('agent_execution_rounds')
