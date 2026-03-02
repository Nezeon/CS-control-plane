import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class Report(Base):
    __tablename__ = "reports"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    report_type = sa.Column(sa.String(50), nullable=False)
    customer_id = sa.Column(sa.Uuid, sa.ForeignKey("customers.id"), nullable=True)
    title = sa.Column(sa.Text, nullable=False)
    content = sa.Column(JSONB, nullable=False)
    period_start = sa.Column(sa.Date, nullable=True)
    period_end = sa.Column(sa.Date, nullable=True)
    generated_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())

    # Relationships
    customer = relationship("Customer", back_populates="reports")

    __table_args__ = (
        sa.Index("idx_reports_type", "report_type"),
        sa.Index("idx_reports_customer", "customer_id"),
        sa.Index("idx_reports_date", generated_at.desc()),
    )
