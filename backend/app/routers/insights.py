import uuid as uuid_mod
from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import cast, Date, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.action_item import ActionItem
from app.models.call_insight import CallInsight
from app.models.customer import Customer
from app.models.user import User
from app.schemas.insight import (
    ActionItemListItem,
    ActionItemStatusUpdate,
    InsightDetail,
    InsightListItem,
    InsightListResponse,
    SentimentTrendItem,
)
from app.schemas.user import CsOwnerBrief

router = APIRouter(prefix="/api/insights", tags=["insights"])


@router.get("", response_model=InsightListResponse)
async def list_insights(
    search: str | None = None,
    customer_id: UUID | None = None,
    sentiment: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List call insights with filters."""
    base = (
        select(CallInsight, Customer.name.label("customer_name"))
        .outerjoin(Customer, CallInsight.customer_id == Customer.id)
    )
    count_q = select(func.count()).select_from(CallInsight)

    if customer_id:
        base = base.where(CallInsight.customer_id == customer_id)
        count_q = count_q.where(CallInsight.customer_id == customer_id)
    if sentiment:
        base = base.where(CallInsight.sentiment == sentiment)
        count_q = count_q.where(CallInsight.sentiment == sentiment)
    if date_from:
        base = base.where(cast(CallInsight.call_date, Date) >= date_from)
        count_q = count_q.where(cast(CallInsight.call_date, Date) >= date_from)
    if date_to:
        base = base.where(cast(CallInsight.call_date, Date) <= date_to)
        count_q = count_q.where(cast(CallInsight.call_date, Date) <= date_to)
    if search:
        search_filter = CallInsight.summary.ilike(f"%{search}%")
        base = base.where(search_filter)
        count_q = count_q.where(search_filter)

    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0

    result = await db.execute(
        base.order_by(CallInsight.call_date.desc()).offset(offset).limit(limit)
    )
    rows = result.all()

    insights = []
    for row in rows:
        ci = row[0]
        customer_name = row.customer_name
        insights.append(InsightListItem(
            id=ci.id,
            customer_id=ci.customer_id,
            customer_name=customer_name,
            call_date=ci.call_date,
            participants=ci.participants or [],
            summary=ci.summary[:300] if ci.summary else None,
            decisions=ci.decisions or [],
            action_items=ci.action_items or [],
            risks=ci.risks or [],
            sentiment=ci.sentiment,
            sentiment_score=ci.sentiment_score,
            key_topics=ci.key_topics or [],
            customer_recap_draft=ci.customer_recap_draft,
            processed_at=ci.processed_at,
        ))

    return InsightListResponse(insights=insights, total=total, limit=limit, offset=offset)


@router.get("/sentiment-trend")
async def get_sentiment_trend(
    days: int = Query(default=30, ge=1, le=365),
    customer_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Sentiment trend over time."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    base = (
        select(
            cast(CallInsight.call_date, Date).label("day"),
            func.avg(CallInsight.sentiment_score).label("avg_score"),
            func.count().label("call_count"),
        )
        .where(CallInsight.call_date >= since)
    )

    if customer_id:
        base = base.where(CallInsight.customer_id == customer_id)

    base = base.group_by(cast(CallInsight.call_date, Date)).order_by(cast(CallInsight.call_date, Date))

    result = await db.execute(base)
    rows = result.all()

    trend = [
        SentimentTrendItem(
            date=str(row.day),
            avg_sentiment_score=round(float(row.avg_score), 2) if row.avg_score else None,
            call_count=row.call_count,
        )
        for row in rows
    ]

    return {"trend": trend}


@router.get("/action-items")
async def list_action_items(
    action_status: str | None = Query(default=None, alias="status"),
    owner_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List action items from call insights."""
    base = (
        select(ActionItem, User.id.label("owner_uid"), User.full_name.label("owner_name"),
               Customer.name.label("customer_name"))
        .outerjoin(User, ActionItem.owner_id == User.id)
        .outerjoin(Customer, ActionItem.customer_id == Customer.id)
    )

    if action_status:
        base = base.where(ActionItem.status == action_status)
    if owner_id:
        base = base.where(ActionItem.owner_id == owner_id)

    base = base.order_by(ActionItem.deadline.asc().nulls_last())

    result = await db.execute(base)
    rows = result.all()

    now = datetime.now(timezone.utc)

    # Count summary
    count_result = await db.execute(
        select(
            func.count().filter(ActionItem.status == "pending").label("pending"),
            func.count().filter(
                ActionItem.status == "pending",
                ActionItem.deadline < now,
            ).label("overdue"),
            func.count().filter(ActionItem.status == "completed").label("completed"),
        )
    )
    summary_row = count_result.first()

    items = []
    for row in rows:
        ai = row[0]
        owner = None
        if row.owner_uid:
            owner = CsOwnerBrief(id=row.owner_uid, full_name=row.owner_name)

        is_overdue = (
            ai.status == "pending"
            and ai.deadline is not None
            and ai.deadline < now
        )

        items.append(ActionItemListItem(
            id=ai.id,
            customer_name=row.customer_name,
            insight_id=ai.source_id,
            task=ai.title,
            owner=owner,
            deadline=ai.deadline,
            status=ai.status,
            is_overdue=is_overdue,
        ))

    return {
        "action_items": items,
        "summary": {
            "pending": summary_row.pending if summary_row else 0,
            "overdue": summary_row.overdue if summary_row else 0,
            "completed": summary_row.completed if summary_row else 0,
        },
    }


@router.get("/{insight_id}", response_model=InsightDetail)
async def get_insight(
    insight_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get full insight detail."""
    result = await db.execute(
        select(CallInsight, Customer.name.label("customer_name"))
        .outerjoin(Customer, CallInsight.customer_id == Customer.id)
        .where(CallInsight.id == insight_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Insight not found")

    ci = row[0]
    return InsightDetail(
        id=ci.id,
        customer_id=ci.customer_id,
        customer_name=row.customer_name,
        fathom_recording_id=ci.fathom_recording_id,
        call_date=ci.call_date,
        participants=ci.participants or [],
        summary=ci.summary,
        decisions=ci.decisions or [],
        action_items=ci.action_items or [],
        risks=ci.risks or [],
        sentiment=ci.sentiment,
        sentiment_score=ci.sentiment_score,
        key_topics=ci.key_topics or [],
        customer_recap_draft=ci.customer_recap_draft,
        raw_transcript=ci.raw_transcript,
        processed_at=ci.processed_at,
    )


@router.post("/sync-fathom", status_code=status.HTTP_202_ACCEPTED)
async def sync_fathom(
    days: int = Query(default=7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Pull recent Fathom meetings and process them through the Call Intelligence agent.

    Fetches meetings from the last `days` days, skips any already imported
    (by fathom_recording_id), and pushes new ones into the event pipeline.
    """
    from app.services.fathom_service import fathom_service, FathomAPIError
    from app.services.event_service import event_service

    if not settings.FATHOM_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Fathom API key not configured",
        )

    since = datetime.now(timezone.utc) - timedelta(days=days)
    created_after = since.strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        meetings = await fathom_service.list_all_meetings(
            created_after=created_after,
            include_transcript=True,
            include_summary=True,
            include_action_items=True,
        )
    except FathomAPIError as e:
        raise HTTPException(status_code=e.status_code or 502, detail=str(e))

    # Check which recording_ids we've already processed
    existing_ids_result = await db.execute(
        select(CallInsight.fathom_recording_id)
        .where(CallInsight.fathom_recording_id.isnot(None))
    )
    existing_ids = {row[0] for row in existing_ids_result.all()}

    imported = 0
    skipped = 0

    for meeting in meetings:
        recording_id = str(meeting.get("recording_id", ""))
        if recording_id in existing_ids:
            skipped += 1
            continue

        transcript_items = meeting.get("transcript", [])
        if not transcript_items:
            skipped += 1
            continue

        transcript_text = fathom_service.build_flat_transcript(transcript_items)
        participants = fathom_service.extract_participants(meeting)
        duration = fathom_service.estimate_duration_minutes(meeting)

        summary_data = meeting.get("default_summary", {})
        fathom_summary = summary_data.get("markdown_formatted") if summary_data else None

        event_payload = {
            "recording_id": recording_id,
            "title": meeting.get("title", "Untitled"),
            "transcript": transcript_text,
            "participants": participants,
            "duration_minutes": duration,
            "fathom_summary": fathom_summary,
            "fathom_action_items": meeting.get("action_items", []),
            "call_date": meeting.get("recording_start_time") or meeting.get("created_at"),
            "fathom_url": meeting.get("url"),
            "share_url": meeting.get("share_url"),
        }

        await event_service.create_and_process_event(
            db_session=db,
            event_type="fathom_recording_ready",
            source="fathom_sync",
            payload=event_payload,
            customer_id=None,
        )
        imported += 1

    return {
        "message": f"Fathom sync complete: {imported} imported, {skipped} skipped",
        "imported": imported,
        "skipped": skipped,
        "total_meetings": len(meetings),
    }


@router.put("/action-items/{item_id}")
async def update_action_item(
    item_id: UUID,
    body: ActionItemStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an action item's status."""
    result = await db.execute(select(ActionItem).where(ActionItem.id == item_id))
    ai = result.scalar_one_or_none()
    if not ai:
        raise HTTPException(status_code=404, detail="Action item not found")

    valid_statuses = {"pending", "in_progress", "completed"}
    if body.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

    ai.status = body.status
    if body.status == "completed" and not ai.completed_at:
        ai.completed_at = datetime.now(timezone.utc)

    await db.commit()

    return {
        "id": ai.id,
        "status": ai.status,
        "completed_at": ai.completed_at,
    }
