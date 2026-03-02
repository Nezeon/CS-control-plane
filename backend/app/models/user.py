import uuid

import sqlalchemy as sa
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    email = sa.Column(sa.String(255), unique=True, nullable=False)
    hashed_password = sa.Column(sa.Text, nullable=False)
    full_name = sa.Column(sa.String(255), nullable=False)
    role = sa.Column(sa.String(50), nullable=False, server_default="cs_engineer")
    avatar_url = sa.Column(sa.Text, nullable=True)
    is_active = sa.Column(sa.Boolean, server_default=sa.text("true"))
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
    updated_at = sa.Column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()
    )

    # Relationships
    owned_customers = relationship("Customer", back_populates="cs_owner", foreign_keys="Customer.cs_owner_id")
    assigned_tickets = relationship("Ticket", back_populates="assigned_to", foreign_keys="Ticket.assigned_to_id")
    assigned_alerts = relationship("Alert", back_populates="assigned_to", foreign_keys="Alert.assigned_to_id")
    owned_action_items = relationship("ActionItem", back_populates="owner", foreign_keys="ActionItem.owner_id")
