"""
Trend Service -- Computes health trends, ticket velocity, and sentiment shifts.

Pure DB queries, no AI calls. Used by the executive summary endpoint
and the alert rules engine.
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.call_insight import CallInsight
from app.models.customer import Customer
from app.models.health_score import HealthScore
from app.models.ticket import Ticket

logger = logging.getLogger("services.trend")


class TrendService:
    """Computes portfolio-level trends from DB data."""

    def health_trends(self, db: Session, days: int = 30) -> dict:
        """
        Portfolio health trend: daily average score + per-customer deltas.

        Returns:
            {
                daily_avg: [{date, avg_score, count}],
                customer_deltas: [{customer_id, name, old_score, new_score, delta}],
                biggest_drops: [...top 5 by negative delta],
                biggest_gains: [...top 5 by positive delta],
            }
        """
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=days)

        # Daily portfolio average
        rows = db.execute(text("""
            SELECT DATE(calculated_at) AS d,
                   ROUND(AVG(score)) AS avg_score,
                   COUNT(DISTINCT customer_id) AS cnt
            FROM health_scores
            WHERE calculated_at >= :start
            GROUP BY DATE(calculated_at)
            ORDER BY d
        """), {"start": start}).fetchall()

        daily_avg = [
            {"date": str(r.d), "avg_score": int(r.avg_score), "count": r.cnt}
            for r in rows
        ]

        # Per-customer: compare earliest vs latest score in window
        deltas = db.execute(text("""
            WITH earliest AS (
                SELECT DISTINCT ON (customer_id) customer_id, score AS old_score
                FROM health_scores
                WHERE calculated_at >= :start
                ORDER BY customer_id, calculated_at ASC
            ),
            latest AS (
                SELECT DISTINCT ON (customer_id) customer_id, score AS new_score
                FROM health_scores
                WHERE calculated_at >= :start
                ORDER BY customer_id, calculated_at DESC
            )
            SELECT c.id AS customer_id, c.name,
                   e.old_score, l.new_score,
                   (l.new_score - e.old_score) AS delta
            FROM customers c
            JOIN earliest e ON e.customer_id = c.id
            JOIN latest l ON l.customer_id = c.id
            ORDER BY delta ASC
        """), {"start": start}).fetchall()

        customer_deltas = [
            {
                "customer_id": str(r.customer_id), "name": r.name,
                "old_score": r.old_score, "new_score": r.new_score,
                "delta": r.delta,
            }
            for r in deltas
        ]

        biggest_drops = [d for d in customer_deltas if d["delta"] < 0][:5]
        biggest_gains = sorted(
            [d for d in customer_deltas if d["delta"] > 0],
            key=lambda x: x["delta"], reverse=True
        )[:5]

        return {
            "daily_avg": daily_avg,
            "customer_deltas": customer_deltas,
            "biggest_drops": biggest_drops,
            "biggest_gains": biggest_gains,
            "period_days": days,
        }

    def ticket_velocity(self, db: Session, days: int = 30) -> dict:
        """
        Ticket creation/resolution rates over time.

        Returns:
            {
                daily: [{date, created, resolved}],
                totals: {created, resolved, net_open},
                by_severity: [{severity, count}],
            }
        """
        start = datetime.now(timezone.utc) - timedelta(days=days)

        daily = db.execute(text("""
            SELECT d.d AS date,
                   COALESCE(c.cnt, 0) AS created,
                   COALESCE(r.cnt, 0) AS resolved
            FROM generate_series(CAST(:start AS date), CURRENT_DATE, '1 day') AS d(d)
            LEFT JOIN (
                SELECT DATE(created_at) AS d, COUNT(*) AS cnt
                FROM tickets WHERE created_at >= :start
                GROUP BY DATE(created_at)
            ) c ON c.d = d.d
            LEFT JOIN (
                SELECT DATE(resolved_at) AS d, COUNT(*) AS cnt
                FROM tickets WHERE resolved_at >= :start
                GROUP BY DATE(resolved_at)
            ) r ON r.d = d.d
            ORDER BY d.d
        """), {"start": start}).fetchall()

        daily_data = [
            {"date": str(r.date), "created": r.created, "resolved": r.resolved}
            for r in daily
        ]

        total_created = sum(d["created"] for d in daily_data)
        total_resolved = sum(d["resolved"] for d in daily_data)

        by_severity = db.execute(text("""
            SELECT severity, COUNT(*) AS count
            FROM tickets WHERE created_at >= :start
            GROUP BY severity ORDER BY count DESC
        """), {"start": start}).fetchall()

        return {
            "daily": daily_data,
            "totals": {
                "created": total_created,
                "resolved": total_resolved,
                "net_open": total_created - total_resolved,
            },
            "by_severity": [
                {"severity": r.severity, "count": r.count} for r in by_severity
            ],
            "period_days": days,
        }

    def sentiment_shifts(self, db: Session, days: int = 30) -> dict:
        """
        Call sentiment distribution and trend.

        Returns:
            {
                distribution: {positive: N, neutral: N, negative: N, mixed: N},
                avg_score: float,
                recent_negative: [{id, customer_name, summary, sentiment}],
            }
        """
        start = datetime.now(timezone.utc) - timedelta(days=days)

        dist = db.execute(text("""
            SELECT sentiment, COUNT(*) AS cnt
            FROM call_insights
            WHERE processed_at >= :start AND sentiment IS NOT NULL
            GROUP BY sentiment
        """), {"start": start}).fetchall()

        distribution = {r.sentiment: r.cnt for r in dist}

        avg = db.execute(text("""
            SELECT AVG(sentiment_score) AS avg_score
            FROM call_insights
            WHERE processed_at >= :start AND sentiment_score IS NOT NULL
        """), {"start": start}).scalar()

        negative = db.execute(text("""
            SELECT ci.id, c.name AS customer_name, ci.summary, ci.sentiment, ci.sentiment_score
            FROM call_insights ci
            LEFT JOIN customers c ON ci.customer_id = c.id
            WHERE ci.processed_at >= :start AND ci.sentiment IN ('negative', 'mixed')
            ORDER BY ci.sentiment_score ASC NULLS LAST
            LIMIT 10
        """), {"start": start}).fetchall()

        return {
            "distribution": distribution,
            "avg_score": round(float(avg), 2) if avg else None,
            "recent_negative": [
                {
                    "id": str(r.id), "customer_name": r.customer_name,
                    "summary": r.summary[:200] if r.summary else "",
                    "sentiment": r.sentiment,
                }
                for r in negative
            ],
            "period_days": days,
        }

    def portfolio_snapshot(self, db: Session) -> dict:
        """
        Current portfolio state: customer counts by risk, tier, renewal proximity.
        """
        # Risk distribution
        risk = db.execute(text("""
            SELECT h.risk_level, COUNT(*) AS cnt
            FROM customers c
            LEFT JOIN LATERAL (
                SELECT risk_level FROM health_scores
                WHERE customer_id = c.id ORDER BY calculated_at DESC LIMIT 1
            ) h ON true
            GROUP BY h.risk_level
        """)).fetchall()

        risk_dist = {r.risk_level or "unknown": r.cnt for r in risk}

        # Tier distribution
        tier = db.execute(text("""
            SELECT tier, COUNT(*) AS cnt FROM customers GROUP BY tier ORDER BY cnt DESC
        """)).fetchall()

        tier_dist = {r.tier or "unknown": r.cnt for r in tier}

        # Upcoming renewals (next 90 days)
        renewals = db.execute(text("""
            SELECT c.id, c.name, c.tier, c.renewal_date, h.score, h.risk_level
            FROM customers c
            LEFT JOIN LATERAL (
                SELECT score, risk_level FROM health_scores
                WHERE customer_id = c.id ORDER BY calculated_at DESC LIMIT 1
            ) h ON true
            WHERE c.renewal_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '90 days'
            ORDER BY c.renewal_date ASC
        """)).fetchall()

        upcoming_renewals = [
            {
                "customer_id": str(r.id), "name": r.name, "tier": r.tier,
                "renewal_date": str(r.renewal_date),
                "health_score": r.score, "risk_level": r.risk_level,
            }
            for r in renewals
        ]

        return {
            "risk_distribution": risk_dist,
            "tier_distribution": tier_dist,
            "upcoming_renewals": upcoming_renewals,
            "total_customers": sum(tier_dist.values()),
        }


trend_service = TrendService()
