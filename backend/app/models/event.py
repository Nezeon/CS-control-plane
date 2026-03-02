import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class Event(Base):
    __tablename__ = "events"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    event_type = sa.Column(sa.String(100), nullable=False)
    source = sa.Column(sa.String(50), nullable=True)
    payload = sa.Column(JSONB, nullable=False)
    status = sa.Column(sa.String(20), server_default="pending")
    routed_to = sa.Column(sa.String(100), nullable=True)
    customer_id = sa.Column(sa.Uuid, sa.ForeignKey("customers.id"), nullable=True)
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
    processed_at = sa.Column(sa.DateTime(timezone=True), nullable=True)

    # Relationships
    customer = relationship("Customer", back_populates="events")

    __table_args__ = (
        sa.Index("idx_events_status", "status"),
        sa.Index("idx_events_type", "event_type"),
        sa.Index("idx_events_date", created_at.desc()),
    )
