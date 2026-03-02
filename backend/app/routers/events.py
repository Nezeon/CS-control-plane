from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.customer import Customer
from app.models.event import Event
from app.models.user import User
from app.schemas.event import (
    EventCreate,
    EventListItem,
    EventListResponse,
    EventResponse,
)

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("", response_model=EventListResponse)
async def list_events(
    event_type: str | None = None,
    source: str | None = None,
    customer_id: str | None = None,
    event_status: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List events with optional filters."""
    base = select(Event, Customer.name.label("customer_name")).outerjoin(
        Customer, Event.customer_id == Customer.id
    )
    count_base = select(func.count()).select_from(Event)

    if event_type:
        base = base.where(Event.event_type == event_type)
        count_base = count_base.where(Event.event_type == event_type)
    if source:
        base = base.where(Event.source == source)
        count_base = count_base.where(Event.source == source)
    if customer_id:
        base = base.where(Event.customer_id == customer_id)
        count_base = count_base.where(Event.customer_id == customer_id)
    if event_status:
        base = base.where(Event.status == event_status)
        count_base = count_base.where(Event.status == event_status)

    total_result = await db.execute(count_base)
    total = total_result.scalar() or 0

    result = await db.execute(
        base.order_by(Event.created_at.desc()).offset(offset).limit(limit)
    )
    rows = result.all()

    events = []
    for row in rows:
        event = row[0]
        customer_name = row.customer_name
        events.append(
            EventListItem(
                id=event.id,
                event_type=event.event_type,
                source=event.source,
                payload=event.payload or {},
                status=event.status,
                routed_to=event.routed_to,
                customer_id=event.customer_id,
                customer_name=customer_name,
                created_at=event.created_at,
                processed_at=event.processed_at,
            )
        )

    return EventListResponse(events=events, total=total, limit=limit, offset=offset)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=EventResponse)
async def create_event(
    body: EventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new event and process it through the pipeline."""
    from app.services.event_service import event_service

    result = await event_service.create_and_process_event(
        db_session=db,
        event_type=body.event_type,
        source=body.source or "api",
        payload=body.payload,
        customer_id=body.customer_id,
    )

    return EventResponse(
        id=result["id"],
        event_type=result["event_type"],
        status=result["status"],
        created_at=result["created_at"],
    )
