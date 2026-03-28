"""Deactivate prospect customers (is_active=False for tier='prospect')

Prospects should be invisible in health checks, dashboards, and customer lists
until their HubSpot deal reaches Closed Won.

Revision ID: j0k1l2m3n4o5
Revises: i9j0k1l2m3n4
Create Date: 2026-03-28
"""
from alembic import op

revision = "j0k1l2m3n4o5"
down_revision = "i9j0k1l2m3n4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "UPDATE customers SET is_active = false WHERE tier = 'prospect' AND is_active = true"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE customers SET is_active = true WHERE tier = 'prospect' AND is_active = false"
    )
