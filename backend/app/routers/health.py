import logging
import uuid as uuid_mod
from datetime import datetime, timedelta, timezone

logger = logging.getLogger("routers.health")

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import cast, Date, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.customer import Customer
from app.models.health_score import HealthScore
from app.models.user import User
from app.schemas.health import (
    HealthScoreItem,
    HealthScoresResponse,
    HealthTrendItem,
    HealthTrendsResponse,
    RunCheckResponse,
)

router = APIRouter(prefix="/api/health", tags=["health"])

AT_RISK_LEVELS = ("high_risk", "critical", "trending_down", "renewal_risk")


def _latest_health_subquery():
    """Row-number subquery to get latest health score per customer."""
    ranked = (
        select(
            HealthScore.customer_id,
            HealthScore.score,
            HealthScore.risk_level,
            HealthScore.risk_flags,
            HealthScore.calculated_at,
            func.row_number()
            .over(
                partition_by=HealthScore.customer_id,
                order_by=HealthScore.calculated_at.desc(),
            )
            .label("rn"),
        )
        .subquery("ranked")
    )
    return select(ranked).where(ranked.c.rn == 1).subquery("latest")


@router.get("/scores", response_model=HealthScoresResponse)
async def get_health_scores(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    latest = _latest_health_subquery()

    result = await db.execute(
        select(
            latest.c.customer_id,
            Customer.name.label("customer_name"),
            latest.c.score,
            latest.c.risk_level,
            latest.c.risk_flags,
            latest.c.calculated_at,
        )
        .join(Customer, Customer.id == latest.c.customer_id)
        .order_by(latest.c.score.asc())
    )
    rows = result.all()

    scores = [
        HealthScoreItem(
            customer_id=row.customer_id,
            customer_name=row.customer_name,
            score=row.score,
            risk_level=row.risk_level,
            risk_flags=row.risk_flags or [],
            calculated_at=row.calculated_at,
        )
        for row in rows
    ]

    return HealthScoresResponse(scores=scores)


@router.get("/at-risk", response_model=HealthScoresResponse)
async def get_at_risk(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    latest = _latest_health_subquery()

    result = await db.execute(
        select(
            latest.c.customer_id,
            Customer.name.label("customer_name"),
            latest.c.score,
            latest.c.risk_level,
            latest.c.risk_flags,
            latest.c.calculated_at,
        )
        .join(Customer, Customer.id == latest.c.customer_id)
        .where(latest.c.risk_level.in_(AT_RISK_LEVELS))
        .order_by(latest.c.score.asc())
    )
    rows = result.all()

    scores = [
        HealthScoreItem(
            customer_id=row.customer_id,
            customer_name=row.customer_name,
            score=row.score,
            risk_level=row.risk_level,
            risk_flags=row.risk_flags or [],
            calculated_at=row.calculated_at,
        )
        for row in rows
    ]

    return HealthScoresResponse(scores=scores)


@router.post("/run-check", status_code=status.HTTP_202_ACCEPTED, response_model=RunCheckResponse)
async def run_health_check(
    current_user: User = Depends(get_current_user),
):
    """Run health check for all customers. Always fires in a background thread."""
    import threading
    from app.tasks.agent_tasks import run_health_check_all

    task_id = str(uuid_mod.uuid4())

    def _run_health_check_bg():
        try:
            run_health_check_all.apply().get()
        except Exception as e:
            logger.error(f"Background health check failed: {e}")

    threading.Thread(target=_run_health_check_bg, daemon=True).start()

    return RunCheckResponse(
        task_id=task_id,
        message="Health check running in background",
        status="processing",
    )


@router.get("/trends", response_model=HealthTrendsResponse)
async def get_health_trends(
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)

    score_date = cast(HealthScore.calculated_at, Date).label("score_date")

    # Daily average score
    result = await db.execute(
        select(
            score_date,
            func.round(func.avg(HealthScore.score), 1).label("avg_score"),
            func.count()
            .filter(HealthScore.risk_level.in_(AT_RISK_LEVELS))
            .label("at_risk_count"),
        )
        .where(HealthScore.calculated_at >= since)
        .group_by(score_date)
        .order_by(score_date.desc())
    )
    rows = result.all()

    daily_averages = [
        HealthTrendItem(
            date=str(row.score_date),
            avg_score=float(row.avg_score),
            at_risk_count=row.at_risk_count,
        )
        for row in rows
    ]

    return HealthTrendsResponse(daily_averages=daily_averages)
