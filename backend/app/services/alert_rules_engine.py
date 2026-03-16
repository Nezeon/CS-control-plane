"""
Alert Rules Engine -- Configurable rules that auto-fire alerts.

Runs as a periodic check (called from health monitor or cron).
Each rule evaluates DB state and creates Alert records when triggered.
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.alert import Alert

logger = logging.getLogger("services.alert_rules")

# Rule definitions: each rule has a name, severity, and a SQL query
# that returns (customer_id, customer_name, detail) rows when triggered.
ALERT_RULES = [
    {
        "name": "health_drop_15",
        "title": "Health score dropped >15 points in 7 days",
        "severity": "high",
        "alert_type": "health_decline",
        "query": """
            WITH latest AS (
                SELECT DISTINCT ON (customer_id) customer_id, score
                FROM health_scores ORDER BY customer_id, calculated_at DESC
            ),
            week_ago AS (
                SELECT DISTINCT ON (customer_id) customer_id, score
                FROM health_scores
                WHERE calculated_at <= NOW() - INTERVAL '7 days'
                ORDER BY customer_id, calculated_at DESC
            )
            SELECT c.id AS customer_id, c.name,
                   w.score AS old_score, l.score AS new_score,
                   (w.score - l.score) AS drop_amount
            FROM customers c
            JOIN latest l ON l.customer_id = c.id
            JOIN week_ago w ON w.customer_id = c.id
            WHERE (w.score - l.score) > 15
        """,
        "detail_template": "Health dropped from {old_score} to {new_score} ({drop_amount} point decline in 7 days)",
        "action_template": "Schedule an urgent check-in call with {name} to identify root causes",
    },
    {
        "name": "critical_tickets_stale",
        "title": "Critical/P1 ticket open >3 days without resolution",
        "severity": "high",
        "alert_type": "sla_breach",
        "query": """
            SELECT c.id AS customer_id, c.name,
                   t.summary, t.severity,
                   EXTRACT(DAY FROM NOW() - t.created_at)::int AS days_open
            FROM tickets t
            JOIN customers c ON t.customer_id = c.id
            WHERE t.severity IN ('P1', 'critical')
              AND t.status NOT IN ('resolved', 'closed')
              AND t.created_at < NOW() - INTERVAL '3 days'
        """,
        "detail_template": "P1 ticket \"{summary}\" open for {days_open} days",
        "action_template": "Escalate {name}'s P1 ticket immediately — SLA at risk",
    },
    {
        "name": "renewal_at_risk",
        "title": "At-risk customer with renewal in <60 days",
        "severity": "critical",
        "alert_type": "renewal_risk",
        "query": """
            SELECT c.id AS customer_id, c.name, c.renewal_date, h.score, h.risk_level
            FROM customers c
            LEFT JOIN LATERAL (
                SELECT score, risk_level FROM health_scores
                WHERE customer_id = c.id ORDER BY calculated_at DESC LIMIT 1
            ) h ON true
            WHERE c.renewal_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '60 days'
              AND h.risk_level IN ('high_risk', 'critical')
        """,
        "detail_template": "Renewal on {renewal_date} with health score {score} ({risk_level})",
        "action_template": "Initiate executive sponsor engagement for {name} before renewal",
    },
    {
        "name": "negative_sentiment_streak",
        "title": "3+ consecutive negative sentiment calls",
        "severity": "medium",
        "alert_type": "sentiment_decline",
        "query": """
            WITH ranked AS (
                SELECT ci.customer_id, c.name, ci.sentiment,
                       ROW_NUMBER() OVER (PARTITION BY ci.customer_id ORDER BY ci.processed_at DESC) AS rn
                FROM call_insights ci
                JOIN customers c ON ci.customer_id = c.id
                WHERE ci.sentiment IS NOT NULL
            )
            SELECT customer_id, name, COUNT(*) AS streak
            FROM ranked
            WHERE rn <= 3 AND sentiment IN ('negative', 'mixed')
            GROUP BY customer_id, name
            HAVING COUNT(*) >= 3
        """,
        "detail_template": "Last {streak} calls had negative/mixed sentiment",
        "action_template": "Review recent call recordings for {name} and identify recurring concerns",
    },
]


class AlertRulesEngine:
    """Evaluates alert rules against DB state and creates alerts."""

    def evaluate_all(self, db: Session) -> dict:
        """
        Run all rules and create alerts for any triggers.

        Returns:
            {rules_checked: int, alerts_created: int, details: [{rule, customer, title}]}
        """
        stats = {"rules_checked": 0, "alerts_created": 0, "details": []}

        for rule in ALERT_RULES:
            stats["rules_checked"] += 1
            try:
                created = self._evaluate_rule(db, rule)
                stats["alerts_created"] += len(created)
                stats["details"].extend(created)
            except Exception as e:
                logger.error(f"[AlertRules] Rule '{rule['name']}' failed: {e}")

        db.commit()
        logger.info(
            f"[AlertRules] Checked {stats['rules_checked']} rules, "
            f"created {stats['alerts_created']} alerts"
        )
        return stats

    def _evaluate_rule(self, db: Session, rule: dict) -> list:
        """Evaluate a single rule and create alerts for matching rows."""
        rows = db.execute(text(rule["query"])).fetchall()
        created = []

        for row in rows:
            row_dict = dict(row._mapping)
            customer_id = row_dict["customer_id"]
            name = row_dict["name"]

            # Skip if an identical alert already exists and is open
            existing = (
                db.query(Alert)
                .filter_by(
                    customer_id=customer_id,
                    alert_type=rule["alert_type"],
                    status="open",
                )
                .first()
            )
            if existing:
                continue

            detail = rule["detail_template"].format(**row_dict)
            action = rule["action_template"].format(**row_dict)

            alert = Alert(
                id=uuid.uuid4(),
                customer_id=customer_id,
                alert_type=rule["alert_type"],
                severity=rule["severity"],
                title=f"{rule['title']} — {name}",
                description=detail,
                suggested_action=action,
                status="open",
            )
            db.add(alert)

            # Send Slack if enabled
            try:
                from app.services.slack_service import slack_service
                if slack_service.configured:
                    db.flush()
                    db.refresh(alert)
                    sent = slack_service.send_alert(alert)
                    if sent:
                        alert.slack_notified = True
            except Exception:
                pass

            created.append({
                "rule": rule["name"],
                "customer": name,
                "title": alert.title,
            })

        return created


alert_rules_engine = AlertRulesEngine()
