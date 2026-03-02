import uuid as uuid_mod
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import cast, Date, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.agent_log import AgentLog
from app.models.call_insight import CallInsight
from app.models.customer import Customer
from app.models.health_score import HealthScore
from app.models.report import Report
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas.report import (
    AgentPerformanceItem,
    AnalyticsResponse,
    GenerateReportRequest,
    HealthHeatmap,
    ReportDetail,
    ReportListItem,
    SentimentDistribution,
    TicketVelocity,
)

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("", response_model=list[ReportListItem])
async def list_reports(
    report_type: str | None = None,
    customer_id: UUID | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List reports with filters."""
    base = (
        select(Report, Customer.name.label("customer_name"))
        .outerjoin(Customer, Report.customer_id == Customer.id)
    )

    if report_type:
        base = base.where(Report.report_type == report_type)
    if customer_id:
        base = base.where(Report.customer_id == customer_id)

    result = await db.execute(
        base.order_by(Report.generated_at.desc()).offset(offset).limit(limit)
    )
    rows = result.all()

    reports = []
    for row in rows:
        report = row[0]
        reports.append(ReportListItem(
            id=report.id,
            report_type=report.report_type,
            title=report.title,
            customer_name=row.customer_name,
            period_start=report.period_start,
            period_end=report.period_end,
            generated_at=report.generated_at,
        ))

    return reports


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Aggregated analytics for the Analytics Lab page."""
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)

    # --- Health Heatmap (customer x day matrix) ---
    customers_result = await db.execute(
        select(Customer.id, Customer.name).order_by(Customer.name)
    )
    customers = customers_result.all()
    customer_names = [c.name for c in customers]
    customer_ids = [c.id for c in customers]

    # Generate date range
    dates = []
    for i in range(days):
        d = (now - timedelta(days=days - 1 - i)).date()
        dates.append(str(d))

    # Get all health scores in range
    hs_result = await db.execute(
        select(
            HealthScore.customer_id,
            cast(HealthScore.calculated_at, Date).label("day"),
            func.avg(HealthScore.score).label("avg_score"),
        )
        .where(HealthScore.calculated_at >= since)
        .group_by(HealthScore.customer_id, cast(HealthScore.calculated_at, Date))
    )
    hs_rows = hs_result.all()

    # Build lookup
    hs_lookup = {}
    for row in hs_rows:
        key = (str(row.customer_id), str(row.day))
        hs_lookup[key] = int(round(float(row.avg_score)))

    scores_matrix = []
    for cid in customer_ids:
        row_scores = []
        for d in dates:
            row_scores.append(hs_lookup.get((str(cid), d)))
        scores_matrix.append(row_scores)

    # --- Ticket Velocity (daily counts by severity) ---
    tv_result = await db.execute(
        select(
            cast(Ticket.created_at, Date).label("day"),
            Ticket.severity,
            func.count().label("cnt"),
        )
        .where(Ticket.created_at >= since)
        .group_by(cast(Ticket.created_at, Date), Ticket.severity)
        .order_by(cast(Ticket.created_at, Date))
    )
    tv_rows = tv_result.all()

    tv_lookup = {}
    for row in tv_rows:
        day_str = str(row.day)
        if day_str not in tv_lookup:
            tv_lookup[day_str] = {"P1": 0, "P2": 0, "P3": 0, "P4": 0}
        if row.severity in tv_lookup[day_str]:
            tv_lookup[day_str][row.severity] = row.cnt

    tv_dates = sorted(tv_lookup.keys())
    p1 = [tv_lookup[d]["P1"] for d in tv_dates]
    p2 = [tv_lookup[d]["P2"] for d in tv_dates]
    p3 = [tv_lookup[d]["P3"] for d in tv_dates]
    p4 = [tv_lookup[d]["P4"] for d in tv_dates]

    # --- Sentiment Distribution (daily counts) ---
    sd_result = await db.execute(
        select(
            cast(CallInsight.call_date, Date).label("day"),
            CallInsight.sentiment,
            func.count().label("cnt"),
        )
        .where(CallInsight.call_date >= since)
        .group_by(cast(CallInsight.call_date, Date), CallInsight.sentiment)
        .order_by(cast(CallInsight.call_date, Date))
    )
    sd_rows = sd_result.all()

    sd_lookup = {}
    for row in sd_rows:
        day_str = str(row.day)
        if day_str not in sd_lookup:
            sd_lookup[day_str] = {"positive": 0, "neutral": 0, "negative": 0}
        if row.sentiment in sd_lookup[day_str]:
            sd_lookup[day_str][row.sentiment] = row.cnt

    sd_dates = sorted(sd_lookup.keys())
    positive = [sd_lookup[d]["positive"] for d in sd_dates]
    neutral = [sd_lookup[d]["neutral"] for d in sd_dates]
    negative = [sd_lookup[d]["negative"] for d in sd_dates]

    # --- Agent Performance ---
    ap_result = await db.execute(
        select(
            AgentLog.agent_name,
            func.count().label("tasks"),
            func.avg(AgentLog.duration_ms).label("avg_ms"),
            func.count().filter(AgentLog.status == "completed").label("success_count"),
        )
        .group_by(AgentLog.agent_name)
    )
    ap_rows = ap_result.all()

    agent_performance = []
    for row in ap_rows:
        rate = round(row.success_count / row.tasks, 2) if row.tasks > 0 else None
        agent_performance.append(AgentPerformanceItem(
            name=row.agent_name,
            tasks=row.tasks,
            success_rate=rate,
            avg_duration_ms=int(row.avg_ms) if row.avg_ms else None,
        ))

    return AnalyticsResponse(
        health_heatmap=HealthHeatmap(
            customers=customer_names,
            dates=dates,
            scores=scores_matrix,
        ),
        ticket_velocity=TicketVelocity(
            dates=tv_dates,
            p1=p1, p2=p2, p3=p3, p4=p4,
        ),
        sentiment_distribution=SentimentDistribution(
            dates=sd_dates,
            positive=positive,
            neutral=neutral,
            negative=negative,
        ),
        agent_performance=agent_performance,
    )


@router.get("/{report_id}", response_model=ReportDetail)
async def get_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get full report detail."""
    result = await db.execute(
        select(Report, Customer.name.label("customer_name"))
        .outerjoin(Customer, Report.customer_id == Customer.id)
        .where(Report.id == report_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")

    report = row[0]
    return ReportDetail(
        id=report.id,
        report_type=report.report_type,
        title=report.title,
        customer_name=row.customer_name,
        customer_id=report.customer_id,
        content=report.content or {},
        period_start=report.period_start,
        period_end=report.period_end,
        generated_at=report.generated_at,
    )


@router.post("/generate", status_code=status.HTTP_202_ACCEPTED)
async def generate_report(
    body: GenerateReportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a new report (mock — creates placeholder)."""
    from app.models.report import Report as ReportModel

    type_titles = {
        "weekly_digest": "Weekly CS Digest",
        "monthly_report": "Monthly CS Report",
        "qbr": "Quarterly Business Review",
    }
    title = type_titles.get(body.report_type, body.report_type.replace("_", " ").title())
    if body.period_start and body.period_end:
        title += f" \u2014 {body.period_start} to {body.period_end}"

    report = ReportModel(
        id=uuid_mod.uuid4(),
        report_type=body.report_type,
        customer_id=body.customer_id,
        title=title,
        content={
            "status": "generating",
            "message": "Report generation in progress...",
        },
        period_start=body.period_start,
        period_end=body.period_end,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    return {
        "task_id": str(uuid_mod.uuid4()),
        "message": f"Generating {title}",
        "status": "processing",
        "report_id": str(report.id),
    }
