"""
Customer Memory Agent (Atlas) — Tier 4 Foundation.

Service agent that builds structured customer context for other agents.
Pipeline: perceive → act (only 2 stages per pipeline.yaml).
Not personality-driven — returns data on demand.

Reports to: Naveen Kapoor (cso_orchestrator)
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.agents.agent_factory import AgentFactory
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

    agent_id = "customer_memory"

    def perceive(self, task: dict) -> dict:
        customer_id = task.get("customer_id")
        self.memory.set_context("customer_id", customer_id)
        return task

    def act(self, task: dict, thinking: dict) -> dict:
        customer_id = task.get("customer_id")
        if not customer_id:
            return {"success": False, "error": "No customer_id provided"}

        db_session = self._current_db
        if not db_session:
            return {"success": False, "error": "No database session"}

        memory_dict = self.build_memory(db_session, customer_id)
        if memory_dict.get("error"):
            return {"success": False, **memory_dict}

        return {"success": True, "output": memory_dict, "reasoning_summary": "Customer context assembled."}

    def build_portfolio_memory(self, db_session: Session) -> dict:
        """
        Build a portfolio-level memory across ALL customers.
        Optimized: TWO queries total (customers+health, tickets+alerts combined).
        """
        from sqlalchemy import text

        # Query 1: customers + latest health score + ticket/alert counts
        result = db_session.execute(text("""
            SELECT
                c.id, c.name, c.industry, c.tier, c.renewal_date,
                h.score AS health_score, h.risk_level, h.risk_flags,
                (SELECT COUNT(*) FROM tickets t WHERE t.customer_id = c.id AND t.status IN ('open', 'in_progress')) AS open_tickets,
                (SELECT COUNT(*) FROM alerts a WHERE a.customer_id = c.id AND a.status IN ('open', 'acknowledged')) AS active_alerts
            FROM customers c
            LEFT JOIN LATERAL (
                SELECT hs.score, hs.risk_level, hs.risk_flags
                FROM health_scores hs
                WHERE hs.customer_id = c.id
                ORDER BY hs.calculated_at DESC
                LIMIT 1
            ) h ON true
            ORDER BY h.score ASC NULLS LAST
        """))
        rows = result.fetchall()

        if not rows:
            return {"error": "No customers found"}

        customer_health = []
        for r in rows:
            customer_health.append({
                "id": str(r.id),
                "name": r.name,
                "industry": r.industry,
                "tier": r.tier,
                "renewal_date": str(r.renewal_date) if r.renewal_date else None,
                "health_score": r.health_score,
                "risk_level": r.risk_level or "unknown",
                "risk_flags": r.risk_flags or [],
                "open_tickets": r.open_tickets or 0,
                "active_alerts": r.active_alerts or 0,
            })

        # Query 2: recent tickets (with customer name) + active alerts in one round-trip
        combo = db_session.execute(text("""
            SELECT * FROM (
                SELECT 'ticket' AS _type, t.id, t.customer_id, t.summary, t.severity, t.status, t.ticket_type AS extra, c.name AS title
                FROM tickets t
                LEFT JOIN customers c ON c.id = t.customer_id
                ORDER BY t.created_at DESC LIMIT 15
            ) tickets
            UNION ALL
            SELECT * FROM (
                SELECT 'alert', a.id, a.customer_id, NULL, a.severity, a.status, a.alert_type, a.title
                FROM alerts a WHERE a.status IN ('open', 'acknowledged') ORDER BY a.created_at DESC LIMIT 10
            ) alerts
        """))
        combo_rows = combo.fetchall()

        ticket_items = []
        alert_items = []
        for r in combo_rows:
            if r._type == "ticket":
                ticket_items.append({
                    "id": str(r.id), "customer_id": str(r.customer_id),
                    "customer_name": r.title or "Unknown",
                    "summary": r.summary, "severity": r.severity,
                    "status": r.status, "type": r.extra,
                })
            else:
                alert_items.append({
                    "id": str(r.id), "type": r.extra,
                    "severity": r.severity, "title": r.title,
                })

        return {
            "customer": {
                "name": "Portfolio (All Customers)",
                "industry": "Mixed",
                "tier": "all",
            },
            "portfolio": {
                "total_customers": len(customer_health),
                "customers": customer_health,
                "at_risk": [c for c in customer_health if c.get("risk_level") in ("high_risk", "critical")],
                "watch_list": [c for c in customer_health if c.get("risk_level") == "watch"],
            },
            "health": {
                "current_score": round(sum(c["health_score"] for c in customer_health if c["health_score"]) / max(1, len([c for c in customer_health if c["health_score"]])), 1) if customer_health else None,
                "risk_level": "high_risk" if any(c.get("risk_level") in ("high_risk", "critical") for c in customer_health) else "watch",
                "risk_flags": [],
                "trend": [],
            },
            "tickets": {
                "total_recent": len(ticket_items),
                "open_count": sum(1 for t in ticket_items if t["status"] in ("open", "in_progress")),
                "items": ticket_items[:10],
            },
            "calls": {"total_recent": 0, "items": []},
            "alerts": alert_items,
            "action_items": [],
        }

    def build_memory(self, db_session: Session, customer_id) -> dict:
        """
        Query database to assemble a structured memory dict.
        Called directly by other agents and by the pipeline.
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


AgentFactory.register("customer_memory", CustomerMemoryAgent)
