"""Add jira_project_key to customers

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2026-03-06
"""
from alembic import op
import sqlalchemy as sa

revision = "d4e5f6g7h8i9"
down_revision = "c3d4e5f6g7h8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("customers", sa.Column("jira_project_key", sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column("customers", "jira_project_key")
