"""
Messages Router — API endpoints for inter-agent message board.

Prefix: /api/v2/messages
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.agent_message import AgentMessage
from app.models.user import User
from app.schemas.message import MessageListResponse, MessageResponse, MessageThreadResponse
from app.services.message_service import message_service

router = APIRouter(prefix="/api/v2/messages", tags=["messages"])


def _build_reply_count_subquery():
    """Subquery: count replies per thread_id."""
    return (
        select(
            AgentMessage.thread_id,
            (func.count() - 1).label("reply_count"),  # exclude the thread starter
        )
        .where(AgentMessage.thread_id.isnot(None))
        .group_by(AgentMessage.thread_id)
        .subquery("reply_counts")
    )


def _format_message(msg: AgentMessage, customer_name: str | None, reply_count: int = 0) -> MessageResponse:
    """Convert an AgentMessage ORM object to the API response schema."""
    return MessageResponse(
        id=msg.id,
        thread_id=msg.thread_id,
        parent_id=msg.parent_id,
        from_agent=msg.from_agent,
        from_name=msg.from_name,
        to_agent=msg.to_agent,
        to_name=msg.to_name,
        message_type=msg.message_type,
        direction=msg.direction,
        content=msg.content,
        priority=msg.priority,
        event_id=msg.event_id,
        customer_name=customer_name,
        status=msg.status,
        created_at=msg.created_at,
        reply_count=reply_count,
    )


@router.get("", response_model=MessageListResponse)
async def list_messages(
    message_type: str | None = Query(default=None, description="Filter by type: task_assignment, deliverable, request, escalation, feedback"),
    agent_id: str | None = Query(default=None, description="Filter by from_agent or to_agent"),
    event_id: UUID | None = Query(default=None, description="Filter by related event"),
    lane: str | None = Query(default=None, description="Filter by lane: support, value, delivery"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List messages with optional filters."""
    rows, total = await message_service.list_messages(
        db=db,
        message_type=message_type,
        agent_id=agent_id,
        event_id=event_id,
        lane=lane,
        limit=limit,
        offset=offset,
    )

    # Build reply count lookup
    reply_sub = _build_reply_count_subquery()
    thread_ids = {row[0].thread_id for row in rows if row[0].thread_id}
    reply_counts = {}
    if thread_ids:
        rc_result = await db.execute(
            select(reply_sub.c.thread_id, reply_sub.c.reply_count).where(
                reply_sub.c.thread_id.in_(thread_ids)
            )
        )
        reply_counts = {r.thread_id: r.reply_count for r in rc_result.all()}

    messages = [
        _format_message(row[0], row.customer_name, reply_counts.get(row[0].thread_id, 0))
        for row in rows
    ]

    return MessageListResponse(messages=messages, total=total, limit=limit, offset=offset)


@router.get("/thread/{thread_id}", response_model=MessageThreadResponse)
async def get_thread(
    thread_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get full conversation thread."""
    try:
        tid = UUID(thread_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid thread_id format — must be a valid UUID")
    rows = await message_service.get_thread(db, tid)
    if not rows:
        raise HTTPException(status_code=404, detail="Thread not found")

    first_msg = rows[0][0]
    messages = [_format_message(row[0], row.customer_name) for row in rows]

    return MessageThreadResponse(
        thread_id=thread_id,
        event_id=first_msg.event_id,
        customer_name=rows[0].customer_name,
        messages=messages,
        total_messages=len(messages),
    )


@router.get("/agent/{agent_id}", response_model=MessageListResponse)
async def get_agent_messages(
    agent_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get messages sent to or from a specific agent."""
    rows, total = await message_service.get_agent_messages(db, agent_id, limit, offset)

    messages = [_format_message(row[0], row.customer_name) for row in rows]

    return MessageListResponse(messages=messages, total=total, limit=limit, offset=offset)


@router.get("/event/{event_id}", response_model=MessageListResponse)
async def get_event_messages(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all messages related to a specific event."""
    rows = await message_service.get_event_messages(db, event_id)

    messages = [_format_message(row[0], row.customer_name) for row in rows]

    return MessageListResponse(messages=messages, total=len(messages), limit=len(messages), offset=0)
