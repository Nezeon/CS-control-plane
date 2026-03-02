import uuid

import sqlalchemy as sa
from sqlalchemy.orm import relationship

from app.database import Base


class ActionItem(Base):
    __tablename__ = "action_items"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    customer_id = sa.Column(sa.Uuid, sa.ForeignKey("customers.id"), nullable=True)
    source_type = sa.Column(sa.String(50), nullable=True)
    source_id = sa.Column(sa.Uuid, nullable=True)
    owner_id = sa.Column(sa.Uuid, sa.ForeignKey("users.id"), nullable=True)
    title = sa.Column(sa.Text, nullable=False)
    description = sa.Column(sa.Text, nullable=True)
    deadline = sa.Column(sa.DateTime(timezone=True), nullable=True)
    status = sa.Column(sa.String(20), server_default="pending")
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
    completed_at = sa.Column(sa.DateTime(timezone=True), nullable=True)

    # Relationships
    customer = relationship("Customer", back_populates="action_items")
    owner = relationship("User", back_populates="owned_action_items", foreign_keys=[owner_id])

    __table_args__ = (
        sa.Index("idx_actions_customer", "customer_id"),
        sa.Index("idx_actions_owner", "owner_id"),
        sa.Index("idx_actions_status", "status"),
        sa.Index(
            "idx_actions_deadline",
            "deadline",
            postgresql_where=sa.text("status = 'pending'"),
        ),
    )
