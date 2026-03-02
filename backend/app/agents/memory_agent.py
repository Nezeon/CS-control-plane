import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.agents.base_agent import BaseAgent
from app.models.action_item import ActionItem
from app.models.alert import Alert
from app.models.call_insight import CallInsight
from app.models.customer import Customer
from app.models.health_score import HealthScore
from app.models.ticket import Ticket

logger = logging.getLogger("agents.customer_memory")


class CustomerMemoryAgent(BaseAgent):
    """Builds structured customer context for other agents."""

    agent_name = "customer_memory"
    agent_type = "control"

    def build_memory(self, db_session: Session, customer_id) -> dict:
        """
        Query database to assemble a structured memory dict.
        This is called directly (not through the event system).
        """
        customer = db_session.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return {"error": f"Customer {customer_id} not found"}

        # Latest health score
        latest_health = (
            db_session.query(HealthScore)
            .filter(HealthScore.customer_id == customer_id)
            .order_by(desc(HealthScore.calculated_at))
            .first()
        )

        # Recent tickets (last 20)
        recent_tickets = (
            db_session.query(Ticket)
            .filter(Ticket.customer_id == customer_id)
            .order_by(desc(Ticket.created_at))
            .limit(20)
            .all()
        )

        # Recent call insights (last 10)
        recent_insights = (
            db_session.query(CallInsight)
            .filter(CallInsight.customer_id == customer_id)
            .order_by(desc(CallInsight.processed_at))
            .limit(10)
            .all()
        )

        # Pending action items
        pending_actions = (
            db_session.query(ActionItem)
            .filter(
                ActionItem.customer_id == customer_id,
                ActionItem.status == "pending",
            )
            .order_by(desc(ActionItem.created_at))
            .all()
        )

        # Active alerts
        active_alerts = (
            db_session.query(Alert)
            .filter(
                Alert.customer_id == customer_id,
                Alert.status.in_(["open", "acknowledged"]),
            )
            .order_by(desc(Alert.created_at))
            .all()
        )

        # Health trend (last 30 days)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        health_trend = (
            db_session.query(HealthScore)
            .filter(
                HealthScore.customer_id == customer_id,
                HealthScore.calculated_at >= thirty_days_ago,
            )
            .order_by(HealthScore.calculated_at)
            .all()
        )

        return {
            "customer": {
                "id": str(customer.id),
                "name": customer.name,
                "industry": customer.industry,
                "tier": customer.tier,
                "contract_start": str(customer.contract_start) if customer.contract_start else None,
                "renewal_date": str(customer.renewal_date) if customer.renewal_date else None,
                "primary_contact": customer.primary_contact_name,
                "deployment_mode": customer.deployment_mode,
                "product_version": customer.product_version,
                "integrations": customer.integrations or [],
                "known_constraints": customer.known_constraints or [],
            },
            "health": {
                "current_score": latest_health.score if latest_health else None,
                "risk_level": latest_health.risk_level if latest_health else None,
                "factors": latest_health.factors if latest_health else {},
                "risk_flags": latest_health.risk_flags if latest_health else [],
                "calculated_at": str(latest_health.calculated_at) if latest_health else None,
                "trend": [
                    {"score": h.score, "date": str(h.calculated_at)}
                    for h in health_trend
                ],
            },
            "tickets": {
                "total_recent": len(recent_tickets),
                "open_count": sum(1 for t in recent_tickets if t.status in ("open", "in_progress")),
                "items": [
                    {
                        "id": str(t.id),
                        "jira_id": t.jira_id,
                        "summary": t.summary,
                        "severity": t.severity,
                        "status": t.status,
                        "type": t.ticket_type,
                        "created_at": str(t.created_at),
                    }
                    for t in recent_tickets
                ],
            },
            "calls": {
                "total_recent": len(recent_insights),
                "items": [
                    {
                        "id": str(ci.id),
                        "summary": ci.summary,
                        "sentiment": ci.sentiment,
                        "sentiment_score": ci.sentiment_score,
                        "key_topics": ci.key_topics or [],
                        "decisions": ci.decisions or [],
                        "call_date": str(ci.call_date),
                    }
                    for ci in recent_insights
                ],
            },
            "action_items": [
                {
                    "id": str(ai.id),
                    "title": ai.title,
                    "deadline": str(ai.deadline) if ai.deadline else None,
                    "source_type": ai.source_type,
                }
                for ai in pending_actions
            ],
            "alerts": [
                {
                    "id": str(a.id),
                    "type": a.alert_type,
                    "severity": a.severity,
                    "title": a.title,
                    "status": a.status,
                }
                for a in active_alerts
            ],
        }

    def execute(self, event: dict, customer_memory: dict) -> dict:
        """No-op — this agent is called directly via build_memory."""
        return {
            "success": True,
            "output": {"message": "Memory agent is used via build_memory(), not events."},
            "reasoning_summary": "No-op execution.",
        }
