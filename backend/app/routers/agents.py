import uuid as uuid_mod
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import cast, Date, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.agent_log import AgentLog
from app.models.customer import Customer
from app.models.event import Event
from app.models.user import User
from app.schemas.agent import (
    AgentInfo,
    AgentListResponse,
    AgentLogItem,
    AgentLogResponse,
    AgentTriggerRequest,
    AgentTriggerResponse,
    OrchestrationFlowItem,
    OrchestrationFlowResponse,
)

router = APIRouter(prefix="/api/agents", tags=["agents"])

# Static registry of all 10 agents
AGENT_REGISTRY = [
    {
        "name": "cs_orchestrator",
        "display_name": "CS Orchestrator",
        "description": "Routes events to the correct agent",
        "lane": "control",
    },
    {
        "name": "customer_memory",
        "display_name": "Customer Memory Agent",
        "description": "Builds structured customer context",
        "lane": "control",
    },
    {
        "name": "call_intelligence",
        "display_name": "Call Intelligence Agent",
        "description": "Extracts insights from call transcripts",
        "lane": "value",
    },
    {
        "name": "health_monitor",
        "display_name": "Health Monitor Agent",
        "description": "Calculates customer health scores",
        "lane": "value",
    },
    {
        "name": "ticket_triage",
        "display_name": "Ticket Triage Agent",
        "description": "Auto-classifies and prioritizes tickets",
        "lane": "support",
    },
    {
        "name": "troubleshooter",
        "display_name": "Troubleshooter Agent",
        "description": "Analyzes support bundles for root cause",
        "lane": "support",
    },
    {
        "name": "escalation_summary",
        "display_name": "Escalation Summary Agent",
        "description": "Generates escalation packages",
        "lane": "support",
    },
    {
        "name": "qbr_value",
        "display_name": "QBR Value Agent",
        "description": "Generates quarterly business review content",
        "lane": "value",
    },
    {
        "name": "sow_prerequisite",
        "display_name": "SOW Prerequisite Agent",
        "description": "Pre-deployment checklists and readiness",
        "lane": "value",
    },
    {
        "name": "deployment_intelligence",
        "display_name": "Deployment Intelligence Agent",
        "description": "Monitors deployment health and patterns",
        "lane": "value",
    },
]

AGENT_NAMES = {a["name"] for a in AGENT_REGISTRY}


async def _enrich_agent(agent_meta: dict, db: AsyncSession) -> AgentInfo:
    """Enrich a static agent entry with live stats from AgentLog."""
    name = agent_meta["name"]
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    # Today's task count
    today_result = await db.execute(
        select(func.count())
        .select_from(AgentLog)
        .where(AgentLog.agent_name == name, AgentLog.created_at >= today)
    )
    tasks_today = today_result.scalar() or 0

    # Total task count
    total_result = await db.execute(
        select(func.count()).select_from(AgentLog).where(AgentLog.agent_name == name)
    )
    tasks_total = total_result.scalar() or 0

    # Average duration
    avg_result = await db.execute(
        select(func.avg(AgentLog.duration_ms))
        .where(AgentLog.agent_name == name, AgentLog.duration_ms.isnot(None))
    )
    avg_ms = avg_result.scalar()
    avg_response_ms = int(avg_ms) if avg_ms else None

    # Success rate
    if tasks_total > 0:
        success_result = await db.execute(
            select(func.count())
            .select_from(AgentLog)
            .where(AgentLog.agent_name == name, AgentLog.status == "completed")
        )
        success_count = success_result.scalar() or 0
        success_rate = round(success_count / tasks_total, 3)
    else:
        success_rate = None

    # Last active
    last_result = await db.execute(
        select(func.max(AgentLog.created_at)).where(AgentLog.agent_name == name)
    )
    last_active = last_result.scalar()

    return AgentInfo(
        name=name,
        display_name=agent_meta["display_name"],
        description=agent_meta["description"],
        lane=agent_meta["lane"],
        status="active" if tasks_today > 0 else "idle",
        tasks_today=tasks_today,
        tasks_total=tasks_total,
        avg_response_ms=avg_response_ms,
        success_rate=success_rate,
        last_active=last_active,
    )


@router.get("", response_model=AgentListResponse)
async def list_agents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all agents with live stats."""
    agents = []
    for meta in AGENT_REGISTRY:
        info = await _enrich_agent(meta, db)
        agents.append(info)
    return AgentListResponse(agents=agents)


@router.get("/orchestration-flow", response_model=OrchestrationFlowResponse)
async def get_orchestration_flow(
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Recent event routing timeline."""
    result = await db.execute(
        select(Event, Customer.name.label("customer_name"))
        .outerjoin(Customer, Event.customer_id == Customer.id)
        .order_by(Event.created_at.desc())
        .limit(limit)
    )
    rows = result.all()

    flows = []
    for row in rows:
        event = row[0]
        customer_name = row.customer_name
        flows.append(
            OrchestrationFlowItem(
                event_id=event.id,
                event_type=event.event_type,
                source=event.source,
                customer_name=customer_name,
                routed_to=event.routed_to,
                status=event.status,
                created_at=event.created_at,
                processed_at=event.processed_at,
            )
        )

    return OrchestrationFlowResponse(flows=flows)


@router.get("/{agent_name}", response_model=AgentInfo)
async def get_agent(
    agent_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get single agent detail."""
    if agent_name not in AGENT_NAMES:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

    meta = next(a for a in AGENT_REGISTRY if a["name"] == agent_name)
    return await _enrich_agent(meta, db)


@router.get("/{agent_name}/logs", response_model=AgentLogResponse)
async def get_agent_logs(
    agent_name: str,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Paginated agent execution logs."""
    if agent_name not in AGENT_NAMES:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

    # Total count
    count_result = await db.execute(
        select(func.count())
        .select_from(AgentLog)
        .where(AgentLog.agent_name == agent_name)
    )
    total = count_result.scalar() or 0

    # Fetch with customer name
    result = await db.execute(
        select(AgentLog, Customer.name.label("customer_name"))
        .outerjoin(Customer, AgentLog.customer_id == Customer.id)
        .where(AgentLog.agent_name == agent_name)
        .order_by(AgentLog.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = result.all()

    logs = []
    for row in rows:
        log = row[0]
        customer_name = row.customer_name
        logs.append(
            AgentLogItem(
                id=log.id,
                agent_name=log.agent_name,
                event_type=log.event_type,
                trigger_event=log.trigger_event,
                customer_name=customer_name,
                input_summary=log.input_summary,
                output_summary=log.output_summary,
                reasoning_summary=log.reasoning_summary,
                status=log.status,
                duration_ms=log.duration_ms,
                created_at=log.created_at,
            )
        )

    return AgentLogResponse(logs=logs, total=total, limit=limit, offset=offset)


@router.post("/{agent_name}/trigger", status_code=status.HTTP_202_ACCEPTED, response_model=AgentTriggerResponse)
async def trigger_agent(
    agent_name: str,
    body: AgentTriggerRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger an agent manually. Uses Celery if available, else runs synchronously."""
    if agent_name not in AGENT_NAMES:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

    # Map agent_name to event_type for orchestrator routing
    agent_to_event = {
        "health_monitor": "manual_health_check",
        "call_intelligence": "zoom_call_completed",
        "ticket_triage": "jira_ticket_created",
        "troubleshooter": "support_bundle_uploaded",
        "escalation_summary": "ticket_escalated",
        "qbr_value": "renewal_approaching",
        "sow_prerequisite": "new_enterprise_customer",
        "deployment_intelligence": "deployment_started",
    }
    event_type = agent_to_event.get(agent_name, f"manual_{agent_name}")

    # Create Event record
    from app.models.event import Event as EventModel

    event_record = EventModel(
        event_type=event_type,
        source="manual_trigger",
        payload={"context": body.context} if body.context else {},
        customer_id=body.customer_id,
    )
    db.add(event_record)
    await db.commit()
    await db.refresh(event_record)

    event_dict = {
        "event_id": event_record.id,
        "event_type": event_type,
        "source": "manual_trigger",
        "payload": event_record.payload,
        "customer_id": body.customer_id,
    }

    # Try Celery, fallback to sync
    task_id = str(uuid_mod.uuid4())
    try:
        from app.tasks.agent_tasks import _is_celery_available, process_event

        if _is_celery_available():
            # Serialize UUIDs for JSON
            serialized = {
                **event_dict,
                "event_id": str(event_dict["event_id"]),
                "customer_id": str(event_dict["customer_id"]),
            }
            result = process_event.apply_async(args=[serialized], task_id=task_id)
            return AgentTriggerResponse(
                task_id=result.id,
                message=f"Agent {agent_name} triggered via Celery",
                status="queued",
            )
    except Exception:
        pass

    # Sync fallback
    try:
        from app.agents.orchestrator import orchestrator
        from app.database import get_sync_session

        sync_db = get_sync_session()
        try:
            # Serialize for orchestrator
            event_dict_sync = {
                **event_dict,
                "event_id": event_record.id,
                "customer_id": body.customer_id,
            }
            route_result = orchestrator.route(sync_db, event_dict_sync)
            agent_result = route_result.get("result", {})

            # Post-processing
            routed_agent = route_result.get("agent_name")
            if agent_result.get("success") and body.customer_id:
                agent_inst = orchestrator.get_agent(routed_agent)
                if routed_agent == "health_monitor" and hasattr(agent_inst, "save_score"):
                    agent_inst.save_score(sync_db, body.customer_id, agent_result)
                elif routed_agent == "call_intelligence" and hasattr(agent_inst, "save_insight"):
                    agent_inst.save_insight(sync_db, body.customer_id, event_dict.get("payload", {}), agent_result)
                elif routed_agent == "troubleshooter" and hasattr(agent_inst, "save_result"):
                    ticket_id = event_dict.get("payload", {}).get("ticket_id")
                    if ticket_id:
                        agent_inst.save_result(sync_db, ticket_id, agent_result)
                elif routed_agent == "escalation_summary" and hasattr(agent_inst, "save_result"):
                    ticket_id = event_dict.get("payload", {}).get("ticket_id")
                    if ticket_id:
                        agent_inst.save_result(sync_db, ticket_id, agent_result)
                elif routed_agent == "qbr_value" and hasattr(agent_inst, "save_report"):
                    agent_inst.save_report(sync_db, body.customer_id, agent_result)

            # Update event record status via async session
            event_record.status = "completed" if agent_result.get("success") else "failed"
            event_record.routed_to = routed_agent
            event_record.processed_at = datetime.now(timezone.utc)
            await db.commit()

            # Broadcast via WebSocket
            from app.websocket_manager import manager
            await manager.broadcast("agent_status", {
                "agent": agent_name,
                "status": "completed" if agent_result.get("success") else "failed",
            })
            await manager.broadcast("event_processed", {
                "event_id": str(event_record.id),
                "event_type": event_type,
                "agent": routed_agent,
                "success": agent_result.get("success", False),
                "customer_id": str(body.customer_id) if body.customer_id else None,
            })

            msg = f"Agent {agent_name} executed synchronously (Celery unavailable)"
            return AgentTriggerResponse(task_id=task_id, message=msg, status="completed")
        finally:
            sync_db.close()
    except Exception as e:
        return AgentTriggerResponse(
            task_id=task_id,
            message=f"Agent {agent_name} failed: {str(e)}",
            status="failed",
        )
