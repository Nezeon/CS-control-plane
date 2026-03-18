import uuid as uuid_mod
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.customer import Customer
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas.ticket import (
    AssigneeBrief,
    CustomerBrief,
    TicketAssign,
    TicketDetail,
    TicketListItem,
    TicketListResponse,
    TicketStatusUpdate,
)

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


def _calc_sla(ticket):
    """Calculate SLA remaining hours and breaching status."""
    if not ticket.sla_deadline:
        return None, False
    now = datetime.now(timezone.utc)
    delta = ticket.sla_deadline - now
    remaining = round(delta.total_seconds() / 3600, 1)
    breaching = remaining <= 0 and ticket.status not in ("resolved", "closed")
    return remaining, breaching


@router.get("", response_model=TicketListResponse)
async def list_tickets(
    search: str | None = None,
    ticket_status: str | None = Query(default=None, alias="status"),
    severity: str | None = None,
    customer_id: UUID | None = None,
    ticket_type: str | None = None,
    assigned_to_id: UUID | None = None,
    sort_by: str = Query(default="created", pattern="^(created|severity|sla)$"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List tickets with filters, sorting, and pagination."""
    base = (
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
    )
    count_q = select(func.count()).select_from(Ticket)

    # Filters
    if search:
        search_filter = or_(
            Ticket.summary.ilike(f"%{search}%"),
            Ticket.jira_id.ilike(f"%{search}%"),
        )
        base = base.where(search_filter)
        count_q = count_q.where(search_filter)
    if ticket_status:
        base = base.where(Ticket.status == ticket_status)
        count_q = count_q.where(Ticket.status == ticket_status)
    if severity:
        base = base.where(Ticket.severity == severity)
        count_q = count_q.where(Ticket.severity == severity)
    if customer_id:
        base = base.where(Ticket.customer_id == customer_id)
        count_q = count_q.where(Ticket.customer_id == customer_id)
    if ticket_type:
        base = base.where(Ticket.ticket_type == ticket_type)
        count_q = count_q.where(Ticket.ticket_type == ticket_type)
    if assigned_to_id:
        base = base.where(Ticket.assigned_to_id == assigned_to_id)
        count_q = count_q.where(Ticket.assigned_to_id == assigned_to_id)

    # Sorting
    sev_order = {"P1": 1, "P2": 2, "P3": 3, "P4": 4}
    if sort_by == "severity":
        order_col = Ticket.severity
    elif sort_by == "sla":
        order_col = Ticket.sla_deadline
    else:
        order_col = Ticket.created_at

    if sort_order == "asc":
        base = base.order_by(order_col.asc().nulls_last())
    else:
        base = base.order_by(order_col.desc().nulls_last())

    # Count
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0

    # Fetch
    result = await db.execute(base.offset(offset).limit(limit))
    rows = result.all()

    tickets = []
    for row in rows:
        ticket = row[0]
        sla_remaining, sla_breaching = _calc_sla(ticket)

        customer = None
        if row.cust_id:
            customer = CustomerBrief(id=row.cust_id, name=row.cust_name)

        assignee = None
        if row.assignee_id:
            assignee = AssigneeBrief(
                id=row.assignee_id,
                full_name=row.assignee_name,
                avatar_url=row.assignee_avatar,
            )

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


@router.get("/{ticket_id}", response_model=TicketDetail)
async def get_ticket(
    ticket_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get full ticket detail with AI analysis results."""
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
        .where(Ticket.id == ticket_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket = row[0]
    sla_remaining, sla_breaching = _calc_sla(ticket)

    customer = None
    if row.cust_id:
        customer = CustomerBrief(id=row.cust_id, name=row.cust_name)

    assignee = None
    if row.assignee_id:
        assignee = AssigneeBrief(
            id=row.assignee_id,
            full_name=row.assignee_name,
            avatar_url=row.assignee_avatar,
        )

    return TicketDetail(
        id=ticket.id,
        jira_id=ticket.jira_id,
        customer=customer,
        summary=ticket.summary,
        description=ticket.description,
        ticket_type=ticket.ticket_type,
        severity=ticket.severity,
        status=ticket.status,
        assigned_to=assignee,
        triage_result=ticket.triage_result,
        troubleshoot_result=ticket.troubleshoot_result,
        escalation_summary=ticket.escalation_summary,
        sla_deadline=ticket.sla_deadline,
        sla_remaining_hours=sla_remaining,
        sla_breaching=sla_breaching,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        resolved_at=ticket.resolved_at,
    )


@router.put("/{ticket_id}/status")
async def update_ticket_status(
    ticket_id: UUID,
    body: TicketStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update ticket status."""
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    valid_statuses = {"open", "in_progress", "waiting", "resolved", "closed"}
    if body.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

    ticket.status = body.status
    if body.status in ("resolved", "closed") and not ticket.resolved_at:
        ticket.resolved_at = datetime.now(timezone.utc)

    await db.commit()

    # Broadcast status change
    from app.websocket_manager import manager
    await manager.broadcast("ticket_status_changed", {
        "ticket_id": str(ticket.id),
        "jira_id": ticket.jira_id,
        "new_status": body.status,
    })

    return {"id": ticket.id, "status": ticket.status, "updated_at": ticket.updated_at}


@router.put("/{ticket_id}/assign")
async def assign_ticket(
    ticket_id: UUID,
    body: TicketAssign,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Assign a ticket to a user."""
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Verify user exists
    user_result = await db.execute(select(User).where(User.id == body.assigned_to_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Assignee user not found")

    ticket.assigned_to_id = body.assigned_to_id
    await db.commit()

    return {"id": ticket.id, "assigned_to_id": ticket.assigned_to_id, "updated_at": ticket.updated_at}


@router.post("/{ticket_id}/triage", status_code=status.HTTP_202_ACCEPTED)
async def triage_ticket(
    ticket_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger AI triage agent for this ticket."""
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    event_dict = {
        "event_type": "jira_ticket_created",
        "source": "manual_trigger",
        "payload": {
            "ticket_id": str(ticket.id),
            "jira_id": ticket.jira_id,
            "summary": ticket.summary,
            "description": ticket.description or "",
            "severity": ticket.severity,
            "ticket_type": ticket.ticket_type,
        },
        "customer_id": str(ticket.customer_id) if ticket.customer_id else None,
    }

    # Try Celery, fallback to sync
    task_id = str(uuid_mod.uuid4())
    try:
        from app.tasks.agent_tasks import _is_celery_available, process_event

        if _is_celery_available():
            result_task = process_event.apply_async(args=[event_dict], task_id=task_id)
            return {
                "task_id": result_task.id,
                "message": f"AI triage initiated for {ticket.jira_id}",
                "status": "processing",
            }
    except Exception:
        pass

    # Sync fallback
    from app.agents.orchestrator import orchestrator
    from app.database import get_sync_session

    sync_db = get_sync_session()
    try:
        route_result = orchestrator.route(sync_db, event_dict)
        agent_result = route_result.get("result", {})

        if agent_result.get("success"):
            ticket.triage_result = agent_result.get("output", {})
            await db.commit()

        return {
            "task_id": task_id,
            "message": f"AI triage completed for {ticket.jira_id}",
            "status": "completed" if agent_result.get("success") else "failed",
        }
    finally:
        sync_db.close()


@router.post("/{ticket_id}/troubleshoot", status_code=status.HTTP_202_ACCEPTED)
async def troubleshoot_ticket(
    ticket_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger AI troubleshooter agent for this ticket."""
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    event_dict = {
        "event_type": "support_bundle_uploaded",
        "source": "manual_trigger",
        "payload": {
            "ticket_id": str(ticket.id),
            "jira_id": ticket.jira_id,
            "summary": ticket.summary,
            "description": ticket.description or "",
            "severity": ticket.severity,
            "ticket_type": ticket.ticket_type,
            "triage_result": ticket.triage_result,
        },
        "customer_id": str(ticket.customer_id) if ticket.customer_id else None,
    }

    task_id = str(uuid_mod.uuid4())
    try:
        from app.tasks.agent_tasks import _is_celery_available, process_event

        if _is_celery_available():
            result_task = process_event.apply_async(args=[event_dict], task_id=task_id)
            return {
                "task_id": result_task.id,
                "message": f"AI troubleshooting initiated for {ticket.jira_id}",
                "status": "processing",
            }
    except Exception:
        pass

    # Sync fallback
    from app.agents.orchestrator import orchestrator
    from app.database import get_sync_session

    sync_db = get_sync_session()
    try:
        route_result = orchestrator.route(sync_db, event_dict)
        agent_result = route_result.get("result", {})

        if agent_result.get("success"):
            ticket.troubleshoot_result = agent_result.get("output", {})
            await db.commit()

        return {
            "task_id": task_id,
            "message": f"AI troubleshooting completed for {ticket.jira_id}",
            "status": "completed" if agent_result.get("success") else "failed",
        }
    finally:
        sync_db.close()


@router.get("/{ticket_id}/similar")
async def get_similar_tickets(
    ticket_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Find similar tickets via RAG vector search."""
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    from app.services import rag_service

    query_text = f"{ticket.summary} {ticket.description or ''}"
    similar = rag_service.find_similar_tickets(query_text, n_results=5)

    similar_issues = []
    for item in similar:
        meta = item.get("metadata", {})
        similar_issues.append({
            "ticket_id": meta.get("jira_id", item.get("id", "N/A")),
            "customer_name": meta.get("customer_name", "Unknown"),
            "summary": item.get("text", "")[:200],
            "status": meta.get("status", "unknown"),
            "severity": meta.get("severity", "N/A"),
            "similarity_score": item.get("similarity", 0),
        })

    return {
        "query_context": ticket.summary,
        "similar_issues": similar_issues,
    }
