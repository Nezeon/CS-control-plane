"""
Fathom Router -- Manual sync triggers and Fathom integration status.

GET  /api/fathom/status    -- Check Fathom API configuration + data freshness
POST /api/fathom/sync      -- Trigger a Fathom meeting sync
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.middleware.auth import get_current_user, require_role
from app.models.user import User

logger = logging.getLogger("routers.fathom")

router = APIRouter(prefix="/api/fathom", tags=["fathom"])


class FathomSyncResponse(BaseModel):
    status: str
    imported: int
    skipped: int
    total: int
    patterns_detected: int
    duration_ms: int


@router.get("/status")
async def fathom_status(current_user: User = Depends(get_current_user)):
    """Check Fathom integration status: API config, last sync, insight count."""
    from app.config import settings
    from app.database import get_sync_session
    from app.models.call_insight import CallInsight
    from sqlalchemy import func

    if not settings.FATHOM_API_KEY:
        return {
            "configured": False,
            "message": "FATHOM_API_KEY not set",
        }

    db = get_sync_session()
    try:
        # Insight count + most recent
        total_insights = db.query(func.count(CallInsight.id)).scalar() or 0
        latest = (
            db.query(func.max(CallInsight.processed_at)).scalar()
        )
        latest_call_date = (
            db.query(func.max(CallInsight.call_date)).scalar()
        )

        # ChromaDB stats
        chromadb_chunks = 0
        try:
            from app.services.meeting_knowledge_service import meeting_knowledge_service
            stats = meeting_knowledge_service.get_collection_stats()
            chromadb_chunks = stats.get("count", 0)
        except Exception:
            pass

        return {
            "configured": True,
            "total_insights": total_insights,
            "last_processed_at": latest.isoformat() if latest else None,
            "latest_call_date": latest_call_date.isoformat() if latest_call_date else None,
            "chromadb_chunks": chromadb_chunks,
        }
    finally:
        db.close()


@router.post("/sync", response_model=FathomSyncResponse)
async def trigger_fathom_sync(
    days: int = Query(14, ge=1, le=730, description="Days back to sync (up to 2 years)"),
    current_user: User = Depends(require_role("admin", "cs_manager")),
):
    """
    Trigger a Fathom meeting sync (admin/manager only).

    Fetches meetings from Fathom API, processes new ones through the
    Fathom agent, and updates the knowledge base. Skips already-imported recordings.
    """
    from app.tasks.agent_tasks import run_fathom_sync

    start = datetime.now(timezone.utc)

    try:
        result = await run_fathom_sync(days=days)
    except Exception as e:
        logger.error(f"[Fathom] Sync failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)[:200]}")

    duration_ms = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)

    if result.get("status") == "error":
        raise HTTPException(status_code=502, detail=result.get("error", "Fathom API error"))

    if result.get("status") == "skipped":
        raise HTTPException(status_code=503, detail=result.get("reason", "Fathom not configured"))

    return FathomSyncResponse(
        status=result.get("status", "ok"),
        imported=result.get("imported", 0),
        skipped=result.get("skipped", 0),
        total=result.get("total", 0),
        patterns_detected=result.get("patterns_detected", 0),
        duration_ms=duration_ms,
    )
