import uuid

import sqlalchemy as sa
from sqlalchemy.orm import relationship

from app.database import Base


class TeachableRule(Base):
    __tablename__ = "teachable_rules"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    rule_text = sa.Column(sa.Text, nullable=False)
    customer_id = sa.Column(sa.Uuid, sa.ForeignKey("customers.id"), nullable=True)  # NULL = global rule
    created_by_slack_user = sa.Column(sa.String(100), nullable=True)
    created_by_name = sa.Column(sa.String(255), nullable=True)
    is_active = sa.Column(sa.Boolean, server_default=sa.text("true"), nullable=False)
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())

    customer = relationship("Customer")

    __table_args__ = (
        sa.Index("idx_teachable_rules_customer_active", "customer_id", "is_active"),
    )
