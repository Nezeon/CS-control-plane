import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class HealthScore(Base):
    __tablename__ = "health_scores"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    customer_id = sa.Column(
        sa.Uuid, sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False
    )
    score = sa.Column(sa.Integer, nullable=False)
    factors = sa.Column(JSONB, nullable=False)
    risk_flags = sa.Column(JSONB, server_default=sa.text("'[]'::jsonb"))
    risk_level = sa.Column(sa.String(20), nullable=True)
    calculated_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())

    # Relationships
    customer = relationship("Customer", back_populates="health_scores")

    __table_args__ = (
        sa.CheckConstraint("score >= 0 AND score <= 100", name="ck_health_score_range"),
        sa.Index("idx_health_customer_date", "customer_id", calculated_at.desc()),
        sa.Index("idx_health_risk_level", "risk_level"),
    )
