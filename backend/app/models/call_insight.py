import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class CallInsight(Base):
    __tablename__ = "call_insights"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    customer_id = sa.Column(sa.Uuid, sa.ForeignKey("customers.id"), nullable=True)
    fathom_recording_id = sa.Column(sa.String(255), nullable=True)
    call_date = sa.Column(sa.DateTime(timezone=True), nullable=False)
    participants = sa.Column(JSONB, server_default=sa.text("'[]'::jsonb"))
    summary = sa.Column(sa.Text, nullable=True)
    decisions = sa.Column(JSONB, server_default=sa.text("'[]'::jsonb"))
    action_items = sa.Column(JSONB, server_default=sa.text("'[]'::jsonb"))
    risks = sa.Column(JSONB, server_default=sa.text("'[]'::jsonb"))
    sentiment = sa.Column(sa.String(20), nullable=True)
    sentiment_score = sa.Column(sa.Float, nullable=True)
    key_topics = sa.Column(JSONB, server_default=sa.text("'[]'::jsonb"))
    customer_recap_draft = sa.Column(sa.Text, nullable=True)
    raw_transcript = sa.Column(sa.Text, nullable=True)
    meeting_type = sa.Column(sa.String(30), nullable=True, server_default=sa.text("'Other'"))
    highlights = sa.Column(JSONB, server_default=sa.text("'[]'::jsonb"))
    conclusion = sa.Column(sa.Text, nullable=True)
    processed_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())

    # Relationships
    customer = relationship("Customer", back_populates="call_insights")

    __table_args__ = (
        sa.Index("idx_insights_customer_date", "customer_id", processed_at.desc()),
        sa.Index("idx_insights_sentiment", "sentiment"),
    )
