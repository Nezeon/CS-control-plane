from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.action_item import ActionItem
from app.models.call_insight import CallInsight
from app.models.customer import Customer
from app.models.health_score import HealthScore
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas.action_item import ActionItemResponse
from app.schemas.customer import (
    CustomerCreate,
    CustomerDetail,
    CustomerListItem,
    CustomerListResponse,
    CustomerUpdate,
    DeploymentInfo,
    HealthInfo,
)
from app.schemas.insight import InsightListItem, InsightListResponse
from app.schemas.ticket import AssigneeBrief, CustomerBrief, TicketListItem, TicketListResponse
from app.schemas.user import CsOwnerBrief

router = APIRouter(prefix="/api/customers", tags=["customers"])


def _build_latest_health_subquery():
    """Subquery: latest health score per customer using row_number()."""
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


def _build_open_ticket_count_subquery():
    """Subquery: count of open tickets per customer."""
    return (
        select(
            Ticket.customer_id,
            func.count().label("open_ticket_count"),
        )
        .where(Ticket.status.notin_(["resolved", "closed"]))
        .group_by(Ticket.customer_id)
        .subquery("open_tickets")
    )


def _build_last_call_subquery():
    """Subquery: most recent call date per customer."""
    return (
        select(
            CallInsight.customer_id,
            func.max(CallInsight.call_date).label("last_call_date"),
        )
        .group_by(CallInsight.customer_id)
        .subquery("last_call")
    )


@router.get("", response_model=CustomerListResponse)
async def list_customers(
    search: str | None = None,
    risk_level: str | None = None,
    cs_owner_id: UUID | None = None,
    tier: str | None = None,
    sort_by: str = Query(default="score", pattern="^(score|name|renewal)$"),
    sort_order: str = Query(default="asc", pattern="^(asc|desc)$"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    latest_health = _build_latest_health_subquery()
    open_tickets = _build_open_ticket_count_subquery()
    last_call = _build_last_call_subquery()

    # Base query
    query = (
        select(
            Customer,
            User.id.label("owner_id"),
            User.full_name.label("owner_name"),
            User.avatar_url.label("owner_avatar"),
            latest_health.c.score.label("health_score"),
            latest_health.c.risk_level.label("risk_level"),
            latest_health.c.risk_flags.label("risk_flags"),
            open_tickets.c.open_ticket_count,
            last_call.c.last_call_date,
        )
        .outerjoin(User, Customer.cs_owner_id == User.id)
        .outerjoin(latest_health, Customer.id == latest_health.c.customer_id)
        .outerjoin(open_tickets, Customer.id == open_tickets.c.customer_id)
        .outerjoin(last_call, Customer.id == last_call.c.customer_id)
        .where(Customer.is_active.is_(True))
    )

    # Count query (before pagination)
    count_query = (
        select(func.count())
        .select_from(Customer)
        .outerjoin(latest_health, Customer.id == latest_health.c.customer_id)
        .where(Customer.is_active.is_(True))
    )

    # Filters
    if search:
        query = query.where(Customer.name.ilike(f"%{search}%"))
        count_query = count_query.where(Customer.name.ilike(f"%{search}%"))
    if risk_level:
        query = query.where(latest_health.c.risk_level == risk_level)
        count_query = count_query.where(latest_health.c.risk_level == risk_level)
    if cs_owner_id:
        query = query.where(Customer.cs_owner_id == cs_owner_id)
        count_query = count_query.where(Customer.cs_owner_id == cs_owner_id)
    if tier:
        query = query.where(Customer.tier == tier)
        count_query = count_query.where(Customer.tier == tier)

    # Sorting
    if sort_by == "score":
        order_col = latest_health.c.score
    elif sort_by == "name":
        order_col = Customer.name
    else:
        order_col = Customer.renewal_date

    if sort_order == "desc":
        query = query.order_by(order_col.desc().nulls_last())
    else:
        query = query.order_by(order_col.asc().nulls_last())

    # Get total
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Pagination
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    rows = result.all()

    today = date.today()
    customers = []
    for row in rows:
        customer = row[0]
        risk_flags = row.risk_flags or []
        renewal = customer.renewal_date
        days_to_renewal = (renewal - today).days if renewal else None

        cs_owner = None
        if row.owner_id:
            cs_owner = CsOwnerBrief(
                id=row.owner_id,
                full_name=row.owner_name,
                avatar_url=row.owner_avatar,
            )

        last_call_dt = row.last_call_date
        last_call_date_val = last_call_dt.date() if last_call_dt else None

        customers.append(
            CustomerListItem(
                id=customer.id,
                name=customer.name,
                industry=customer.industry,
                tier=customer.tier,
                health_score=row.health_score,
                risk_level=row.risk_level,
                risk_count=len(risk_flags),
                open_ticket_count=row.open_ticket_count or 0,
                cs_owner=cs_owner,
                renewal_date=renewal,
                days_to_renewal=days_to_renewal,
                last_call_date=last_call_date_val,
                primary_contact_name=customer.primary_contact_name,
            )
        )

    return CustomerListResponse(
        customers=customers, total=total, limit=limit, offset=offset
    )


@router.get("/{customer_id}", response_model=CustomerDetail)
async def get_customer(
    customer_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    # Get customer with owner
    result = await db.execute(
        select(Customer, User)
        .outerjoin(User, Customer.cs_owner_id == User.id)
        .where(Customer.id == customer_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Customer not found")

    customer, owner = row[0], row[1]

    # Latest health score
    hs_result = await db.execute(
        select(HealthScore)
        .where(HealthScore.customer_id == customer_id)
        .order_by(HealthScore.calculated_at.desc())
        .limit(1)
    )
    latest_hs = hs_result.scalar_one_or_none()

    # Open ticket count
    tc_result = await db.execute(
        select(func.count())
        .select_from(Ticket)
        .where(Ticket.customer_id == customer_id)
        .where(Ticket.status.notin_(["resolved", "closed"]))
    )
    open_ticket_count = tc_result.scalar() or 0

    # Recent call count (last 30 days)
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    cc_result = await db.execute(
        select(func.count())
        .select_from(CallInsight)
        .where(CallInsight.customer_id == customer_id)
        .where(CallInsight.call_date >= thirty_days_ago)
    )
    recent_call_count = cc_result.scalar() or 0

    # Pending action items count
    ai_result = await db.execute(
        select(func.count())
        .select_from(ActionItem)
        .where(ActionItem.customer_id == customer_id)
        .where(ActionItem.status == "pending")
    )
    pending_action_items = ai_result.scalar() or 0

    today = date.today()
    days_to_renewal = (customer.renewal_date - today).days if customer.renewal_date else None

    cs_owner = None
    if owner:
        cs_owner = CsOwnerBrief(
            id=owner.id, full_name=owner.full_name, avatar_url=owner.avatar_url
        )

    deployment = DeploymentInfo(
        mode=customer.deployment_mode,
        product_version=customer.product_version,
        integrations=customer.integrations or [],
        known_constraints=customer.known_constraints or [],
    )

    health = HealthInfo(
        current_score=latest_hs.score if latest_hs else None,
        risk_level=latest_hs.risk_level if latest_hs else None,
        risk_flags=latest_hs.risk_flags or [] if latest_hs else [],
        factors=latest_hs.factors or {} if latest_hs else {},
    )

    return CustomerDetail(
        id=customer.id,
        name=customer.name,
        industry=customer.industry,
        tier=customer.tier,
        contract_start=customer.contract_start,
        renewal_date=customer.renewal_date,
        days_to_renewal=days_to_renewal,
        primary_contact_name=customer.primary_contact_name,
        primary_contact_email=customer.primary_contact_email,
        cs_owner=cs_owner,
        deployment=deployment,
        health=health,
        open_ticket_count=open_ticket_count,
        recent_call_count=recent_call_count,
        pending_action_items=pending_action_items,
        metadata=customer.metadata_ or {},
        created_at=customer.created_at,
        updated_at=customer.updated_at,
    )


@router.get("/{customer_id}/health-history")
async def get_health_history(
    customer_id: UUID,
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    # Verify customer exists
    cust_result = await db.execute(
        select(Customer.id).where(Customer.id == customer_id)
    )
    if not cust_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Customer not found")

    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(HealthScore)
        .where(HealthScore.customer_id == customer_id)
        .where(HealthScore.calculated_at >= since)
        .order_by(HealthScore.calculated_at.desc())
    )
    scores = result.scalars().all()

    history = [
        {
            "date": hs.calculated_at.strftime("%Y-%m-%d"),
            "score": hs.score,
            "risk_level": hs.risk_level,
            "risk_flags": hs.risk_flags or [],
        }
        for hs in scores
    ]

    return {"customer_id": customer_id, "history": history}


@router.get("/{customer_id}/tickets", response_model=TicketListResponse)
async def get_customer_tickets(
    customer_id: UUID,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    # Count
    count_result = await db.execute(
        select(func.count())
        .select_from(Ticket)
        .where(Ticket.customer_id == customer_id)
    )
    total = count_result.scalar() or 0

    # Fetch with explicit joins (no lazy loading in async)
    result = await db.execute(
        select(
            Ticket,
            Customer.id.label("cust_id"),
            Customer.name.label("cust_name"),
            User.id.label("assignee_id"),
            User.full_name.label("assignee_name"),
            User.avatar_url.label("assignee_avatar"),
        )
        .outerjoin(Customer, Ticket.customer_id == Customer.id)
        .outerjoin(User, Ticket.assigned_to_id == User.id)
        .where(Ticket.customer_id == customer_id)
        .order_by(Ticket.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = result.all()

    tickets = []
    for row in rows:
        ticket = row[0]
        sla_remaining, sla_breaching = None, False
        if ticket.sla_deadline:
            delta = ticket.sla_deadline - datetime.now(timezone.utc)
            sla_remaining = round(delta.total_seconds() / 3600, 1)
            sla_breaching = sla_remaining <= 0 and ticket.status not in ("resolved", "closed")

        customer = CustomerBrief(id=row.cust_id, name=row.cust_name) if row.cust_id else None
        assignee = AssigneeBrief(id=row.assignee_id, full_name=row.assignee_name, avatar_url=row.assignee_avatar) if row.assignee_id else None

        tickets.append(TicketListItem(
            id=ticket.id,
            jira_id=ticket.jira_id,
            customer=customer,
            summary=ticket.summary,
            ticket_type=ticket.ticket_type,
            severity=ticket.severity,
            status=ticket.status,
            assigned_to=assignee,
            has_triage_result=ticket.triage_result is not None,
            has_troubleshoot_result=ticket.troubleshoot_result is not None,
            sla_deadline=ticket.sla_deadline,
            sla_remaining_hours=sla_remaining,
            sla_breaching=sla_breaching,
            created_at=ticket.created_at,
            updated_at=ticket.updated_at,
        ))

    return TicketListResponse(tickets=tickets, total=total, limit=limit, offset=offset)


@router.get("/{customer_id}/insights", response_model=InsightListResponse)
async def get_customer_insights(
    customer_id: UUID,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    count_result = await db.execute(
        select(func.count())
        .select_from(CallInsight)
        .where(CallInsight.customer_id == customer_id)
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(CallInsight)
        .where(CallInsight.customer_id == customer_id)
        .order_by(CallInsight.call_date.desc())
        .offset(offset)
        .limit(limit)
    )
    insights = result.scalars().all()

    return InsightListResponse(
        insights=[InsightListItem.model_validate(i) for i in insights],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{customer_id}/action-items")
async def get_customer_action_items(
    customer_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ActionItem, User)
        .outerjoin(User, ActionItem.owner_id == User.id)
        .where(ActionItem.customer_id == customer_id)
        .order_by(ActionItem.created_at.desc())
    )
    rows = result.all()

    action_items = []
    for row in rows:
        ai, owner = row[0], row[1]
        owner_brief = None
        if owner:
            owner_brief = CsOwnerBrief(
                id=owner.id, full_name=owner.full_name, avatar_url=owner.avatar_url
            )
        action_items.append(
            ActionItemResponse(
                id=ai.id,
                title=ai.title,
                description=ai.description,
                source_type=ai.source_type,
                source_id=ai.source_id,
                owner=owner_brief,
                deadline=ai.deadline,
                status=ai.status,
                created_at=ai.created_at,
            )
        )

    return {"action_items": action_items}


@router.get("/{customer_id}/similar-issues")
async def get_similar_issues(
    customer_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Find similar issues using RAG vector search on recent tickets."""
    from app.services import rag_service

    # Get the customer's most recent ticket for context
    ticket_result = await db.execute(
        select(Ticket)
        .where(Ticket.customer_id == customer_id)
        .order_by(Ticket.created_at.desc())
        .limit(1)
    )
    recent_ticket = ticket_result.scalar_one_or_none()

    if not recent_ticket:
        return {"query_context": None, "similar_issues": []}

    query_text = f"{recent_ticket.summary} {recent_ticket.description or ''}"
    similar = rag_service.find_similar_tickets(query_text, n_results=5)

    if not similar:
        return {
            "query_context": recent_ticket.summary,
            "similar_issues": [],
        }

    similar_issues = []
    for item in similar:
        meta = item.get("metadata", {})
        similar_issues.append({
            "ticket_id": meta.get("jira_id", item.get("id", "N/A")),
            "customer_name": meta.get("customer_name", "Unknown"),
            "summary": item.get("text", "")[:200],
            "resolution": meta.get("resolution", "N/A"),
            "status": meta.get("status", "unknown"),
            "severity": meta.get("severity", "N/A"),
            "similarity_score": item.get("similarity", 0),
        })

    return {
        "query_context": recent_ticket.summary,
        "similar_issues": similar_issues,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_customer(
    body: CustomerCreate,
    db: AsyncSession = Depends(get_db),
):
    customer = Customer(
        name=body.name,
        industry=body.industry,
        tier=body.tier,
        contract_start=body.contract_start,
        renewal_date=body.renewal_date,
        primary_contact_name=body.primary_contact_name,
        primary_contact_email=body.primary_contact_email,
        cs_owner_id=body.cs_owner_id,
        deployment_mode=body.deployment_mode,
        product_version=body.product_version,
        integrations=body.integrations,
        known_constraints=body.known_constraints,
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)

    return {
        "id": customer.id,
        "name": customer.name,
        "industry": customer.industry,
        "tier": customer.tier,
        "contract_start": customer.contract_start,
        "renewal_date": customer.renewal_date,
        "primary_contact_name": customer.primary_contact_name,
        "primary_contact_email": customer.primary_contact_email,
        "cs_owner_id": customer.cs_owner_id,
        "deployment_mode": customer.deployment_mode,
        "product_version": customer.product_version,
        "integrations": customer.integrations,
        "known_constraints": customer.known_constraints,
        "created_at": customer.created_at,
        "updated_at": customer.updated_at,
    }


@router.put("/{customer_id}")
async def update_customer(
    customer_id: UUID,
    body: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(customer, field, value)

    await db.commit()
    await db.refresh(customer)

    return {
        "id": customer.id,
        "name": customer.name,
        "industry": customer.industry,
        "tier": customer.tier,
        "contract_start": customer.contract_start,
        "renewal_date": customer.renewal_date,
        "primary_contact_name": customer.primary_contact_name,
        "primary_contact_email": customer.primary_contact_email,
        "cs_owner_id": customer.cs_owner_id,
        "deployment_mode": customer.deployment_mode,
        "product_version": customer.product_version,
        "integrations": customer.integrations,
        "known_constraints": customer.known_constraints,
        "created_at": customer.created_at,
        "updated_at": customer.updated_at,
    }


# ── Customer Memory (ARCHITECTURE.md Section 4.4) ────────────────────


@router.get("/{customer_id}/memory")
async def get_customer_memory(
    customer_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get the full Customer Memory JSON for a customer."""
    from app.database import get_sync_session

    cust_result = await db.execute(
        select(Customer).where(Customer.id == customer_id)
    )
    customer = cust_result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    sync_db = get_sync_session()
    try:
        from app.agents.memory_agent import CustomerMemoryAgent
        memory_agent = CustomerMemoryAgent()
        return memory_agent.build_memory(sync_db, str(customer_id))
    except Exception as e:
        return {
            "customer": {
                "id": str(customer.id),
                "name": customer.name,
                "industry": customer.industry,
                "tier": customer.tier,
                "deployment_mode": customer.deployment_mode,
                "product_version": customer.product_version,
                "integrations": customer.integrations or [],
                "known_constraints": customer.known_constraints or [],
                "renewal_date": str(customer.renewal_date) if customer.renewal_date else None,
                "current_health": customer.current_health,
            },
            "error": str(e),
        }
    finally:
        sync_db.close()


@router.put("/{customer_id}/memory")
async def update_customer_memory(
    customer_id: UUID,
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    """Update specific Customer Memory fields (safe fields only)."""
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    allowed_fields = {
        "known_constraints", "integrations", "metadata_",
        "deployment_mode", "product_version",
    }
    updated = {}
    for key, value in body.items():
        if key in allowed_fields:
            setattr(customer, key, value)
            updated[key] = value

    if not updated:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    await db.commit()
    return {"updated_fields": list(updated.keys()), "customer_id": str(customer_id)}
