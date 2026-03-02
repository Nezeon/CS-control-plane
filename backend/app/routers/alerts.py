from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.alert import Alert
from app.models.customer import Customer
from app.models.user import User
from app.schemas.alert import AlertListItem, AlertListResponse, CustomerBrief
from app.schemas.user import CsOwnerBrief

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("", response_model=AlertListResponse)
async def list_alerts(
    alert_status: str | None = Query(default=None, alias="status"),
    severity: str | None = None,
    customer_id: UUID | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List alerts with filters."""
    base = (
        select(
            Alert,
            Customer.id.label("cust_id"),
            Customer.name.label("cust_name"),
            User.id.label("assignee_id"),
            User.full_name.label("assignee_name"),
            User.avatar_url.label("assignee_avatar"),
        )
        .outerjoin(Customer, Alert.customer_id == Customer.id)
        .outerjoin(User, Alert.assigned_to_id == User.id)
    )
    count_q = select(func.count()).select_from(Alert)

    if alert_status:
        base = base.where(Alert.status == alert_status)
        count_q = count_q.where(Alert.status == alert_status)
    if severity:
        base = base.where(Alert.severity == severity)
        count_q = count_q.where(Alert.severity == severity)
    if customer_id:
        base = base.where(Alert.customer_id == customer_id)
        count_q = count_q.where(Alert.customer_id == customer_id)

    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0

    result = await db.execute(
        base.order_by(Alert.created_at.desc()).offset(offset).limit(limit)
    )
    rows = result.all()

    alerts = []
    for row in rows:
        alert = row[0]

        customer = None
        if row.cust_id:
            customer = CustomerBrief(id=row.cust_id, name=row.cust_name)

        assigned_to = None
        if row.assignee_id:
            assigned_to = CsOwnerBrief(
                id=row.assignee_id,
                full_name=row.assignee_name,
                avatar_url=row.assignee_avatar,
            )

        alerts.append(AlertListItem(
            id=alert.id,
            customer=customer,
            alert_type=alert.alert_type,
            severity=alert.severity,
            title=alert.title,
            description=alert.description,
            suggested_action=alert.suggested_action,
            similar_past_issues=alert.similar_past_issues or [],
            assigned_to=assigned_to,
            status=alert.status,
            slack_notified=alert.slack_notified,
            created_at=alert.created_at,
        ))

    return AlertListResponse(alerts=alerts, total=total, limit=limit, offset=offset)


async def _update_alert_status(alert_id: UUID, new_status: str, db: AsyncSession):
    """Helper to update alert status and broadcast."""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = new_status
    if new_status == "resolved":
        alert.resolved_at = datetime.now(timezone.utc)

    await db.commit()

    from app.websocket_manager import manager
    await manager.broadcast("alert_updated", {
        "alert_id": str(alert.id),
        "new_status": new_status,
        "customer_id": str(alert.customer_id) if alert.customer_id else None,
    })

    return {"id": alert.id, "status": alert.status, "resolved_at": alert.resolved_at}


@router.put("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Acknowledge an alert."""
    return await _update_alert_status(alert_id, "acknowledged", db)


@router.put("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Resolve an alert."""
    return await _update_alert_status(alert_id, "resolved", db)


@router.put("/{alert_id}/dismiss")
async def dismiss_alert(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dismiss an alert."""
    return await _update_alert_status(alert_id, "dismissed", db)
