"""
Chat Router — User-facing AI chat endpoints.

POST /api/chat/send              — Send a message, returns immediately (~50ms)
GET  /api/chat/conversations     — List user's conversations
GET  /api/chat/conversations/{id} — Get conversation with all messages
DELETE /api/chat/conversations/{id} — Archive a conversation

The agent pipeline runs in a background thread after POST /send returns.
The answer arrives via WebSocket (chat:message_complete).
"""

import asyncio
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi.security import OAuth2PasswordBearer

from app.database import get_db, get_sync_session
from app.middleware.auth import get_current_user
from app.models.chat_conversation import ChatConversation
from app.models.chat_message import ChatMessage
from app.models.customer import Customer
from app.models.user import User
from app.utils.security import decode_token
from app.schemas.chat import (
    ChatConversationDetailResponse,
    ChatConversationListResponse,
    ChatConversationSummary,
    ChatMessageResponse,
    ChatSendRequest,
    ChatSendResponse,
)

logger = logging.getLogger("routers.chat")

router = APIRouter(prefix="/api/chat", tags=["chat"])

_oauth2_chat = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def _get_user_id_fast(token: str = Depends(_oauth2_chat)) -> uuid.UUID:
    """Lightweight auth for chat /send — trusts JWT claims, skips DB lookup."""
    payload = decode_token(token)
    uid = payload.get("sub")
    if not uid or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token")
    return uuid.UUID(uid)


@router.post("/send", response_model=ChatSendResponse)
async def send_message(
    body: ChatSendRequest,
    user_id: uuid.UUID = Depends(_get_user_id_fast),
):
    """
    Send a user chat message and trigger agent orchestration.

    Returns immediately with status="processing" (~50ms).
    The agent pipeline runs in a background thread.
    The actual answer arrives via WebSocket (chat:message_complete).
    """
    from app.services.chat_service import chat_service

    # Generate IDs upfront — no DB needed
    conversation_id = body.conversation_id or uuid.uuid4()
    message_id = uuid.uuid4()
    assistant_message_id = uuid.uuid4()

    logger.info(f"[ChatRouter] POST /send from user={user_id}, conv={conversation_id}")

    # BACKGROUND: Create records AND run fast path in a single thread
    loop = asyncio.get_event_loop()
    loop.run_in_executor(
        None,
        chat_service.process_message_full,
        str(user_id),
        body.message,
        str(body.customer_id) if body.customer_id else None,
        str(conversation_id),
        str(message_id),
        str(assistant_message_id),
    )

    # Return IMMEDIATELY (~1ms) — no DB call
    return ChatSendResponse(
        conversation_id=conversation_id,
        message_id=message_id,
        event_id=None,
        status="processing",
    )


@router.get("/conversations", response_model=ChatConversationListResponse)
async def list_conversations(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List the current user's chat conversations, most recent first."""
    # Count total
    count_q = select(func.count(ChatConversation.id)).where(
        ChatConversation.user_id == current_user.id,
        ChatConversation.status == "active",
    )
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0

    # Fetch conversations
    q = (
        select(ChatConversation)
        .where(
            ChatConversation.user_id == current_user.id,
            ChatConversation.status == "active",
        )
        .order_by(desc(ChatConversation.updated_at))
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(q)
    conversations = result.scalars().all()

    summaries = []
    for conv in conversations:
        # Get message count and last message time
        msg_q = select(
            func.count(ChatMessage.id),
            func.max(ChatMessage.created_at),
        ).where(ChatMessage.conversation_id == conv.id)
        msg_result = await db.execute(msg_q)
        msg_count, last_msg_at = msg_result.one()

        # Get customer name if linked
        customer_name = None
        if conv.customer_id:
            cust_q = select(Customer.name).where(Customer.id == conv.customer_id)
            cust_result = await db.execute(cust_q)
            customer_name = cust_result.scalar()

        summaries.append(ChatConversationSummary(
            id=conv.id,
            title=conv.title,
            customer_id=conv.customer_id,
            customer_name=customer_name,
            message_count=msg_count or 0,
            last_message_at=last_msg_at,
            status=conv.status,
            created_at=conv.created_at,
        ))

    return ChatConversationListResponse(conversations=summaries, total=total)


@router.get("/conversations/{conversation_id}", response_model=ChatConversationDetailResponse)
async def get_conversation(
    conversation_id: uuid.UUID,
    user_id: uuid.UUID = Depends(_get_user_id_fast),
):
    """Get a conversation with all its messages. Uses sync DB for speed."""
    from sqlalchemy.orm import Session as SyncSession

    db: SyncSession = get_sync_session()
    try:
        conv = (
            db.query(ChatConversation)
            .filter(ChatConversation.id == conversation_id, ChatConversation.user_id == user_id)
            .first()
        )
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")

        messages = (
            db.query(ChatMessage)
            .filter(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at)
            .all()
        )

        customer_name = None
        if conv.customer_id:
            customer_name = db.query(Customer.name).filter(Customer.id == conv.customer_id).scalar()

        return ChatConversationDetailResponse(
            id=conv.id,
            title=conv.title,
            customer_id=conv.customer_id,
            customer_name=customer_name,
            status=conv.status,
            messages=[
                ChatMessageResponse(
                    id=m.id,
                    conversation_id=m.conversation_id,
                    role=m.role,
                    content=m.content,
                    event_id=m.event_id,
                    agents_involved=m.agents_involved or [],
                    pipeline_status=m.pipeline_status,
                    execution_metadata=m.execution_metadata or {},
                    created_at=m.created_at,
                )
                for m in messages
            ],
            created_at=conv.created_at,
        )
    finally:
        db.close()


@router.delete("/conversations/{conversation_id}")
async def archive_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Archive a conversation (soft delete)."""
    q = select(ChatConversation).where(
        ChatConversation.id == conversation_id,
        ChatConversation.user_id == current_user.id,
    )
    result = await db.execute(q)
    conv = result.scalar_one_or_none()

    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conv.status = "archived"
    await db.commit()
    return {"status": "archived", "id": str(conversation_id)}


# ── Teachable Rules API ──────────────────────────────────────────────

@router.get("/rules")
async def list_rules(
    customer_id: uuid.UUID | None = Query(None, description="Filter by customer (omit for all)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List active teachable rules, optionally filtered by customer."""
    from app.models.teachable_rule import TeachableRule

    q = select(TeachableRule).where(TeachableRule.is_active == True)
    if customer_id:
        q = q.where(TeachableRule.customer_id == customer_id)
    q = q.order_by(desc(TeachableRule.created_at)).limit(50)

    result = await db.execute(q)
    rules = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "rule_text": r.rule_text,
            "customer_id": str(r.customer_id) if r.customer_id else None,
            "created_by_name": r.created_by_name,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rules
    ]


@router.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft-delete a teachable rule."""
    from app.models.teachable_rule import TeachableRule

    result = await db.execute(
        select(TeachableRule).where(TeachableRule.id == rule_id, TeachableRule.is_active == True)
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    rule.is_active = False
    await db.commit()
    return {"status": "deleted", "id": str(rule_id)}
