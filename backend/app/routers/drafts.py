"""
Drafts API — View and manage agent draft outputs.

Supports listing, filtering, and approving/dismissing drafts from the dashboard
(in addition to Slack interactive buttons).
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

router = APIRouter(prefix="/api/drafts", tags=["drafts"])


@router.get("")
async def list_drafts(
    status: Optional[str] = Query(None, description="Filter by status: pending, approved, edited, dismissed"),
    agent_id: Optional[str] = Query(None, description="Filter by agent_id"),
    customer_id: Optional[str] = Query(None, description="Filter by customer_id"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List drafts with optional filters."""
    from sqlalchemy import select
    from app.models.agent_draft import AgentDraft

    q = select(AgentDraft).order_by(desc(AgentDraft.created_at))

    if status:
        q = q.where(AgentDraft.status == status)
    if agent_id:
        q = q.where(AgentDraft.agent_id == agent_id)
    if customer_id:
        try:
            cid = uuid.UUID(customer_id)
            q = q.where(AgentDraft.customer_id == cid)
        except ValueError:
            pass

    q = q.offset(offset).limit(limit)
    result = await db.execute(q)
    drafts = result.scalars().all()

    return [
        {
            "id": str(d.id),
            "agent_id": d.agent_id,
            "event_id": str(d.event_id) if d.event_id else None,
            "customer_id": str(d.customer_id) if d.customer_id else None,
            "draft_type": d.draft_type,
            "draft_content": d.draft_content,
            "status": d.status,
            "confidence": d.confidence,
            "slack_channel": d.slack_channel,
            "approved_by": d.approved_by,
            "approved_at": d.approved_at.isoformat() if d.approved_at else None,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in drafts
    ]


@router.get("/{draft_id}")
async def get_draft(draft_id: str, db: AsyncSession = Depends(get_db)):
    """Get a single draft by ID."""
    from sqlalchemy import select
    from app.models.agent_draft import AgentDraft

    try:
        did = uuid.UUID(draft_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid draft ID")

    result = await db.execute(select(AgentDraft).where(AgentDraft.id == did))
    draft = result.scalar_one_or_none()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    return {
        "id": str(draft.id),
        "agent_id": draft.agent_id,
        "event_id": str(draft.event_id) if draft.event_id else None,
        "customer_id": str(draft.customer_id) if draft.customer_id else None,
        "draft_type": draft.draft_type,
        "draft_content": draft.draft_content,
        "status": draft.status,
        "confidence": draft.confidence,
        "slack_channel": draft.slack_channel,
        "slack_message_ts": draft.slack_message_ts,
        "approved_by": draft.approved_by,
        "approved_at": draft.approved_at.isoformat() if draft.approved_at else None,
        "edit_diff": draft.edit_diff,
        "created_at": draft.created_at.isoformat() if draft.created_at else None,
    }


@router.post("/{draft_id}/approve")
async def approve_draft_endpoint(draft_id: str):
    """Approve a draft from the dashboard."""
    from app.database import get_sync_session
    from app.services import draft_service

    sync_db = get_sync_session()
    try:
        draft = draft_service.approve_draft(sync_db, draft_id, approved_by="dashboard_user")
        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found")
        return {"status": "approved", "draft_id": str(draft.id)}
    finally:
        sync_db.close()


@router.post("/{draft_id}/dismiss")
async def dismiss_draft_endpoint(draft_id: str):
    """Dismiss a draft from the dashboard."""
    from app.database import get_sync_session
    from app.services import draft_service

    sync_db = get_sync_session()
    try:
        draft = draft_service.dismiss_draft(sync_db, draft_id, dismissed_by="dashboard_user")
        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found")
        return {"status": "dismissed", "draft_id": str(draft.id)}
    finally:
        sync_db.close()
