"""
HubSpot Router -- Manual sync triggers and HubSpot integration status.

GET  /api/hubspot/status          -- Check HubSpot integration status
POST /api/hubspot/sync            -- Trigger a full sync
POST /api/hubspot/sync/{deal_id}  -- Sync a single deal
GET  /api/hubspot/pipelines       -- List pipeline stages
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.config import settings
from app.middleware.auth import get_current_user, require_role
from app.models.user import User

logger = logging.getLogger("routers.hubspot")

router = APIRouter(prefix="/api/hubspot", tags=["hubspot"])


class SyncRequest(BaseModel):
    trigger_events: bool = True


class SyncResponse(BaseModel):
    created: int
    updated: int
    skipped: int
    errors: int
    total: int
    duration_ms: int


@router.get("/status")
async def hubspot_status(current_user: User = Depends(get_current_user)):
    """Check if HubSpot integration is configured and reachable."""
    from app.services.hubspot_service import hubspot_service

    if not hubspot_service.configured:
        return {
            "configured": False,
            "message": "HubSpot credentials not set (HUBSPOT_ACCESS_TOKEN)",
        }

    # Try a lightweight API call to verify credentials
    try:
        data = hubspot_service.list_deals(limit=1)
        deal_count = len(data.get("results", []))
        return {
            "configured": True,
            "reachable": True,
            "deals_found": deal_count > 0,
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
    """Trigger HubSpot deal sync (admin/manager only)."""
    from app.tasks.hubspot_sync import sync_hubspot_deals

    start = datetime.now(timezone.utc)

    try:
        stats = sync_hubspot_deals(trigger_events=body.trigger_events)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"[HubSpot] Sync failed: {e}", exc_info=True)
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


@router.post("/sync/{deal_id}")
async def sync_single(
    deal_id: str,
    trigger_events: bool = Query(True),
    current_user: User = Depends(require_role("admin", "cs_manager")),
):
    """Sync a single HubSpot deal by ID."""
    from app.tasks.hubspot_sync import sync_single_deal

    try:
        result = sync_single_deal(deal_id, trigger_events=trigger_events)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"[HubSpot] Single sync failed for {deal_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)[:200]}")

    return {
        "deal_id": deal_id,
        "action": result["action"],
        "internal_id": str(result["deal_id"]),
    }


@router.get("/pipelines")
async def list_pipelines(current_user: User = Depends(get_current_user)):
    """List all HubSpot deal pipelines with stages."""
    from app.services.hubspot_service import hubspot_service

    if not hubspot_service.configured:
        raise HTTPException(status_code=503, detail="HubSpot not configured")

    try:
        pipelines = hubspot_service.list_pipelines()
        return {"pipelines": pipelines}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch pipelines: {str(e)[:200]}")
