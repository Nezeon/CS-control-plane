"""
Executive Summary Router -- Portfolio-level trends, alerts, and insights.

GET  /api/executive/summary     -- Full executive summary (trends + snapshot + alerts)
GET  /api/executive/trends      -- Health/ticket/sentiment trends only
POST /api/executive/check-rules -- Run alert rules engine manually
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, get_sync_session
from app.middleware.auth import get_current_user, require_role
from app.models.user import User

logger = logging.getLogger("routers.executive")

router = APIRouter(prefix="/api/executive", tags=["executive"])


@router.get("/summary")
async def executive_summary(
    days: int = Query(default=30, ge=7, le=90),
    current_user: User = Depends(get_current_user),
):
    """
    Full executive summary: portfolio snapshot, health trends,
    ticket velocity, sentiment shifts, and upcoming renewals.
    """
    from app.services.trend_service import trend_service

    db = get_sync_session()
    try:
        snapshot = trend_service.portfolio_snapshot(db)
        health = trend_service.health_trends(db, days=days)
        tickets = trend_service.ticket_velocity(db, days=days)
        sentiment = trend_service.sentiment_shifts(db, days=days)

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "period_days": days,
            "portfolio": snapshot,
            "health_trends": health,
            "ticket_velocity": tickets,
            "sentiment": sentiment,
        }
    finally:
        db.close()


@router.get("/trends")
async def trends_only(
    days: int = Query(default=30, ge=7, le=90),
    current_user: User = Depends(get_current_user),
):
    """Health trends + ticket velocity (lighter than full summary)."""
    from app.services.trend_service import trend_service

    db = get_sync_session()
    try:
        health = trend_service.health_trends(db, days=days)
        tickets = trend_service.ticket_velocity(db, days=days)
        return {"health_trends": health, "ticket_velocity": tickets}
    finally:
        db.close()


@router.post("/check-rules")
async def check_alert_rules(
    current_user: User = Depends(require_role("admin", "cs_manager")),
):
    """
    Manually trigger the alert rules engine (admin/manager only).
    Evaluates all rules and creates alerts for any matches.
    """
    from app.services.alert_rules_engine import alert_rules_engine

    db = get_sync_session()
    try:
        stats = alert_rules_engine.evaluate_all(db)
        return stats
    finally:
        db.close()
