from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, cast, Date, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.agent_log import AgentLog
from app.models.customer import Customer
from app.models.event import Event
from app.models.health_score import HealthScore
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas.dashboard import (
    DashboardAgentItem,
    DashboardEventItem,
    DashboardEventsResponse,
    DashboardStats,
    QuickHealthItem,
    TrendData,
)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def _latest_health_subquery():
    """Latest health score per customer."""
    ranked = (
        select(
            HealthScore.customer_id,
            HealthScore.score,
            HealthScore.risk_level,
            HealthScore.risk_flags,
            func.row_number()
            .over(
                partition_by=HealthScore.customer_id,
                order_by=HealthScore.calculated_at.desc(),
            )
            .label("rn"),
        )
        .subquery("ranked_health")
    )
    return select(ranked).where(ranked.c.rn == 1).subquery("latest_health")


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
):
    """Aggregated KPIs with 7-day trend comparison."""
    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=7)

    # Total customers
    total_result = await db.execute(select(func.count()).select_from(Customer))
    total_customers = total_result.scalar() or 0

    # Latest health per customer
    latest = _latest_health_subquery()

    # At-risk count (current)
    risk_result = await db.execute(
        select(func.count())
        .select_from(latest)
        .where(latest.c.risk_level.in_(["high_risk", "critical"]))
    )
    at_risk_count = risk_result.scalar() or 0

    # Open P0/P1 tickets (current)
    open_result = await db.execute(
        select(func.count())
        .select_from(Ticket)
        .where(
            Ticket.status.notin_(["resolved", "closed"]),
            Ticket.severity.in_(["P0", "P1"]),
        )
    )
    open_tickets = open_result.scalar() or 0

    # Avg health score (current)
    avg_result = await db.execute(
        select(func.avg(latest.c.score)).select_from(latest)
    )
    avg_raw = avg_result.scalar()
    avg_health_score = round(float(avg_raw), 1) if avg_raw is not None else None

    # --- Trends (compare with 7 days ago) ---
    old_cust_result = await db.execute(
        select(func.count())
        .select_from(Customer)
        .where(Customer.created_at <= seven_days_ago)
    )
    old_customers = old_cust_result.scalar() or 0
    customers_change = total_customers - old_customers

    # Open P0/P1 tickets 7 days ago
    old_tickets_result = await db.execute(
        select(func.count())
        .select_from(Ticket)
        .where(
            Ticket.created_at <= seven_days_ago,
            Ticket.status.notin_(["resolved", "closed"]),
            Ticket.severity.in_(["P0", "P1"]),
        )
    )
    old_open_tickets = old_tickets_result.scalar() or 0
    tickets_change = open_tickets - old_open_tickets

    # Health 7 days ago
    old_health_result = await db.execute(
        select(func.avg(HealthScore.score))
        .where(
            cast(HealthScore.calculated_at, Date)
            == cast(seven_days_ago, Date)
        )
    )
    old_avg = old_health_result.scalar()
    health_change = round(float(avg_raw) - float(old_avg), 1) if avg_raw and old_avg else 0.0

    # Risk 7 days ago
    old_risk_result = await db.execute(
        select(func.count())
        .where(
            HealthScore.risk_level.in_(["high_risk", "critical"]),
            cast(HealthScore.calculated_at, Date)
            == cast(seven_days_ago, Date),
        )
    )
    old_risk = old_risk_result.scalar() or 0
    risk_change = at_risk_count - old_risk

    return DashboardStats(
        total_customers=total_customers,
        at_risk_count=at_risk_count,
        open_tickets=open_tickets,
        avg_health_score=avg_health_score,
        trends=TrendData(
            customers_change=customers_change,
            risk_change=risk_change,
            tickets_change=tickets_change,
            health_change=health_change,
        ),
    )


@router.get("/agents", response_model=list[DashboardAgentItem])
async def get_dashboard_agents(
    db: AsyncSession = Depends(get_db),
):
    """All 13 agents with live stats (single batch query)."""
    from app.routers.agents import AGENT_REGISTRY

    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    # Batch: one query for all agents instead of N round-trips
    result = await db.execute(
        select(
            AgentLog.agent_name,
            func.count().filter(AgentLog.created_at >= today).label("tasks_today"),
            func.avg(AgentLog.duration_ms).filter(AgentLog.duration_ms.isnot(None)).label("avg_ms"),
            func.max(AgentLog.created_at).label("last_active"),
        )
        .group_by(AgentLog.agent_name)
    )
    stats = {row.agent_name: row for row in result.all()}

    agents = []
    for i, meta in enumerate(AGENT_REGISTRY):
        name = meta["name"]
        row = stats.get(name)
        tasks_today = (row.tasks_today or 0) if row else 0
        avg_ms = row.avg_ms if row else None

        agents.append(DashboardAgentItem(
            id=f"agent-{i + 1:02d}",
            agent_key=meta.get("agent_key", name),
            name=name,
            display_name=meta["display_name"],
            human_name=meta.get("human_name"),
            tier=meta.get("tier", 3),
            lane=meta["lane"],
            role=meta.get("role"),
            status="active" if tasks_today > 0 else "idle",
            tasks_today=tasks_today,
            avg_response_ms=int(avg_ms) if avg_ms else None,
            last_active=row.last_active if row else None,
            manages=meta.get("manages", []),
        ))

    return agents


EVENT_DESCRIPTIONS = {
    "jira_ticket_created": "New ticket created",
    "jira_ticket_updated": "Ticket updated",
    "ticket_escalated": "Ticket escalated",
    "support_bundle_uploaded": "Support bundle received",
    "zoom_call_completed": "Call completed",
    "fathom_recording_ready": "Call recording processed",
    "daily_health_check": "Daily health check",
    "manual_health_check": "Manual health check",
    "renewal_approaching": "Renewal approaching",
    "new_enterprise_customer": "New enterprise customer",
    "deployment_started": "Deployment initiated",
}


@router.get("/events", response_model=DashboardEventsResponse)
async def get_dashboard_events(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Latest events for the live feed."""
    count_result = await db.execute(select(func.count()).select_from(Event))
    total = count_result.scalar() or 0

    result = await db.execute(
        select(Event, Customer.name.label("customer_name"))
        .outerjoin(Customer, Event.customer_id == Customer.id)
        .order_by(Event.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = result.all()

    events = []
    for row in rows:
        event = row[0]
        customer_name = row.customer_name

        base_desc = EVENT_DESCRIPTIONS.get(event.event_type, event.event_type)
        payload = event.payload or {}
        summary = payload.get("summary", "")
        if customer_name and summary:
            description = f"{base_desc}: {summary[:80]} ({customer_name})"
        elif customer_name:
            description = f"{base_desc} for {customer_name}"
        else:
            description = base_desc

        if event.routed_to:
            description += f" \u2192 {event.routed_to}"

        events.append(DashboardEventItem(
            id=event.id,
            event_type=event.event_type,
            source=event.source,
            description=description,
            customer_name=customer_name,
            routed_to=event.routed_to,
            status=event.status,
            created_at=event.created_at,
            processed_at=event.processed_at,
        ))

    return DashboardEventsResponse(events=events, total=total, limit=limit, offset=offset)


@router.get("/quick-health", response_model=list[QuickHealthItem])
async def get_quick_health(
    db: AsyncSession = Depends(get_db),
):
    """All customers sorted by risk (worst first), with ticket counts."""
    latest = _latest_health_subquery()
    open_tickets = (
        select(
            Ticket.customer_id,
            func.count().label("open_ticket_count"),
        )
        .where(Ticket.status.notin_(["resolved", "closed"]))
        .group_by(Ticket.customer_id)
        .subquery("open_tickets")
    )

    result = await db.execute(
        select(
            Customer.id,
            Customer.name,
            latest.c.score,
            latest.c.risk_level,
            latest.c.risk_flags,
            open_tickets.c.open_ticket_count,
        )
        .outerjoin(latest, Customer.id == latest.c.customer_id)
        .outerjoin(open_tickets, Customer.id == open_tickets.c.customer_id)
        .order_by(
            case(
                (latest.c.risk_level == "critical", 0),
                (latest.c.risk_level == "high_risk", 1),
                (latest.c.risk_level == "watch", 2),
                else_=3,
            ).asc(),
            latest.c.score.asc().nulls_last(),
        )
    )
    rows = result.all()

    items = []
    for row in rows:
        name = row.name
        words = name.split()
        initial = "".join(w[0].upper() for w in words[:2]) if words else "?"
        risk_flags = row.risk_flags or []

        items.append(QuickHealthItem(
            id=row.id,
            name=name,
            health_score=row.score,
            risk_level=row.risk_level,
            risk_count=len(risk_flags),
            open_ticket_count=row.open_ticket_count or 0,
            initial=initial,
        ))

    return items
