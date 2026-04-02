"""
Jira Router -- Manual sync triggers and Jira integration status.

POST /api/jira/sync          -- Trigger a full or incremental sync
POST /api/jira/sync/{key}    -- Sync a single Jira issue
GET  /api/jira/status        -- Check Jira integration status
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.config import settings
from app.middleware.auth import get_current_user, require_role
from app.models.user import User

logger = logging.getLogger("routers.jira")

router = APIRouter(prefix="/api/jira", tags=["jira"])


class SyncRequest(BaseModel):
    since: str | None = None  # ISO date for incremental sync
    project_keys: list[str] | None = None
    trigger_triage: bool = True


class SyncResponse(BaseModel):
    created: int
    updated: int
    skipped: int
    errors: int
    total: int
    duration_ms: int


@router.get("/status")
async def jira_status(current_user: User = Depends(get_current_user)):
    """Check if Jira integration is configured and reachable."""
    from app.services.jira_service import jira_service

    if not jira_service.configured:
        return {
            "configured": False,
            "message": "Jira credentials not set (JIRA_API_URL, JIRA_EMAIL, JIRA_API_TOKEN)",
        }

    # Try a lightweight API call to verify credentials
    try:
        data = jira_service.search_issues(f"project = {settings.JIRA_DEFAULT_PROJECT}", max_results=1)
        return {
            "configured": True,
            "reachable": True,
            "issues_found": len(data.get("issues", [])) > 0,
        }
    except Exception as e:
        return {
            "configured": True,
            "reachable": False,
            "error": str(e)[:200],
        }


@router.post("/sync", response_model=SyncResponse)
async def trigger_sync(
    body: SyncRequest,
    current_user: User = Depends(require_role("admin", "cs_manager")),
):
    """
    Trigger Jira ticket sync (admin/manager only).

    - No `since` = full sync of all open tickets
    - With `since` = incremental sync (only tickets updated after that date)
    """
    from app.tasks.jira_sync import sync_jira_tickets

    start = datetime.now(timezone.utc)

    try:
        stats = sync_jira_tickets(
            since=body.since,
            project_keys=body.project_keys,
            trigger_triage=body.trigger_triage,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"[Jira] Sync failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)[:200]}")

    duration_ms = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)

    return SyncResponse(
        created=stats["created"],
        updated=stats["updated"],
        skipped=stats["skipped"],
        errors=stats["errors"],
        total=stats["total"],
        duration_ms=duration_ms,
    )


@router.post("/sync/{jira_key}")
async def sync_single(
    jira_key: str,
    trigger_triage: bool = Query(True),
    current_user: User = Depends(require_role("admin", "cs_manager")),
):
    """Sync a single Jira issue by key (e.g. CS-123)."""
    from app.tasks.jira_sync import sync_single_issue

    try:
        result = sync_single_issue(jira_key, trigger_triage=trigger_triage)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"[Jira] Single sync failed for {jira_key}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)[:200]}")

    return {
        "issue": jira_key,
        "action": result["action"],
        "ticket_id": str(result["ticket_id"]),
    }


@router.post("/relink-orphaned")
async def relink_orphaned_tickets(
    current_user: User = Depends(require_role("admin", "cs_manager")),
):
    """
    Re-run customer matching on all tickets with customer_id = NULL.

    Fixes tickets that were synced before improved matching logic or
    before the customer was added to the database.
    """
    from app.database import get_sync_session
    from app.models.ticket import Ticket
    from app.tasks.jira_sync import _resolve_customer_from_summary, _build_customer_cache

    db = get_sync_session()
    try:
        orphaned = db.query(Ticket).filter(Ticket.customer_id.is_(None)).all()
        customer_cache = _build_customer_cache(db)
        linked = 0
        matched = {}
        for ticket in orphaned:
            customer_id, customer_name = _resolve_customer_from_summary(
                db, ticket.summary or "", customer_cache=customer_cache
            )
            if customer_id:
                ticket.customer_id = customer_id
                linked += 1
                matched[customer_name] = matched.get(customer_name, 0) + 1
        db.commit()
        return {
            "orphaned_total": len(orphaned),
            "relinked": linked,
            "still_orphaned": len(orphaned) - linked,
            "by_customer": matched,
        }
    except Exception as e:
        db.rollback()
        logger.error(f"[Jira] Relink failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)[:200])
    finally:
        db.close()
