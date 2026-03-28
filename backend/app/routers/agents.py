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
    # Tier 1: Supervisor
    {
        "name": "cso_orchestrator",
        "agent_key": "cso_orchestrator",
        "display_name": "CS Orchestrator",
        "human_name": "Naveen Kapoor",
        "tier": 1,
        "lane": "control",
        "role": "CS Manager",
        "description": "Strategic decomposition, delegation, quality evaluation, synthesis",
        "manages": ["triage_agent", "troubleshooter", "escalation_summary", "health_monitor", "qbr_value", "sow_prerequisite", "deployment_intelligence"],
    },
    # Specialists — Support
    {
        "name": "triage_agent",
        "agent_key": "triage_agent",
        "display_name": "Ticket Triage Specialist",
        "human_name": "Kai Nakamura",
        "tier": 3,
        "lane": "support",
        "role": "Triage Specialist",
        "description": "Auto-classifies and prioritizes tickets",
        "manages": [],
    },
    {
        "name": "troubleshooter_agent",
        "agent_key": "troubleshooter_agent",
        "display_name": "Troubleshooting Engineer",
        "human_name": "Leo Petrov",
        "tier": 3,
        "lane": "support",
        "role": "Troubleshooting Engineer",
        "description": "Root-cause analysis, RAG-powered troubleshooting",
        "manages": [],
    },
    {
        "name": "escalation_agent",
        "agent_key": "escalation_agent",
        "display_name": "Escalation Manager",
        "human_name": "Maya Santiago",
        "tier": 3,
        "lane": "support",
        "role": "Escalation Manager",
        "description": "Escalation management, stakeholder communication",
        "manages": [],
    },
    # Tier 3: Specialists — Value
    {
        "name": "health_monitor_agent",
        "agent_key": "health_monitor_agent",
        "display_name": "Customer Health Analyst",
        "human_name": "Dr. Aisha Okafor",
        "tier": 3,
        "lane": "value",
        "role": "Health Analyst",
        "description": "Calculates customer health scores, trend analysis",
        "manages": [],
    },
    {
        "name": "qbr_agent",
        "agent_key": "qbr_agent",
        "display_name": "QBR & Review Specialist",
        "human_name": "Sofia Marquez",
        "tier": 3,
        "lane": "value",
        "role": "QBR Specialist",
        "description": "Generates quarterly business review content",
        "manages": [],
    },
    # Tier 3: Specialists — Delivery
    {
        "name": "sow_agent",
        "agent_key": "sow_agent",
        "display_name": "Scope & SOW Specialist",
        "human_name": "Ethan Brooks",
        "tier": 3,
        "lane": "delivery",
        "role": "SOW Specialist",
        "description": "SOW analysis, milestone tracking, scope management",
        "manages": [],
    },
    {
        "name": "deployment_intel_agent",
        "agent_key": "deployment_intel_agent",
        "display_name": "Deployment Intelligence Analyst",
        "human_name": "Zara Kim",
        "tier": 3,
        "lane": "delivery",
        "role": "Deployment Analyst",
        "description": "Monitors deployment health and patterns",
        "manages": [],
    },
    # Tier 3: Specialists — Pre-Sales
    {
        "name": "presales_funnel",
        "agent_key": "presales_funnel",
        "display_name": "Pre-Sales Funnel Analyst",
        "human_name": "Rachel Simmons",
        "tier": 3,
        "lane": "presales",
        "role": "Pipeline Analyst",
        "description": "Analyzes HubSpot pipeline: conversion rates, stalled deals, blocker patterns",
        "manages": [],
    },
    # Tier 4: Foundation
    {
        "name": "customer_memory",
        "agent_key": "customer_memory",
        "display_name": "Customer Memory Manager",
        "human_name": "Atlas",
        "tier": 4,
        "lane": "control",
        "role": "Memory Manager",
        "description": "Institutional memory, context retrieval, cross-agent knowledge",
        "manages": [],
    },
]

AGENT_NAMES = {a["name"] for a in AGENT_REGISTRY}


async def _batch_agent_stats(db: AsyncSession) -> dict:
    """Fetch all agent stats in a single query instead of N+1."""
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    result = await db.execute(
        select(
            AgentLog.agent_name,
            func.count().label("tasks_total"),
            func.count().filter(AgentLog.created_at >= today).label("tasks_today"),
            func.avg(AgentLog.duration_ms).filter(AgentLog.duration_ms.isnot(None)).label("avg_ms"),
            func.count().filter(AgentLog.status == "completed").label("success_count"),
            func.max(AgentLog.created_at).label("last_active"),
        )
        .group_by(AgentLog.agent_name)
    )
    rows = result.all()

    stats = {}
    for row in rows:
        total = row.tasks_total or 0
        stats[row.agent_name] = {
            "tasks_today": row.tasks_today or 0,
            "tasks_total": total,
            "avg_response_ms": int(row.avg_ms) if row.avg_ms else None,
            "success_rate": round((row.success_count or 0) / total, 3) if total > 0 else None,
            "last_active": row.last_active,
        }
    return stats


async def _enrich_agent(agent_meta: dict, db: AsyncSession) -> AgentInfo:
    """Enrich a single agent with live stats (used for detail endpoint)."""
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    name = agent_meta["name"]

    result = await db.execute(
        select(
            func.count().label("tasks_total"),
            func.count().filter(AgentLog.created_at >= today).label("tasks_today"),
            func.avg(AgentLog.duration_ms).filter(AgentLog.duration_ms.isnot(None)).label("avg_ms"),
            func.count().filter(AgentLog.status == "completed").label("success_count"),
            func.max(AgentLog.created_at).label("last_active"),
        )
        .where(AgentLog.agent_name == name)
    )
    row = result.one()
    total = row.tasks_total or 0

    return AgentInfo(
        id=agent_meta.get("agent_key", name),
        agent_key=agent_meta.get("agent_key", name),
        name=name,
        display_name=agent_meta["display_name"],
        human_name=agent_meta.get("human_name"),
        description=agent_meta["description"],
        tier=agent_meta.get("tier", 3),
        lane=agent_meta["lane"],
        role=agent_meta.get("role"),
        status="active" if (row.tasks_today or 0) > 0 else "idle",
        tasks_today=row.tasks_today or 0,
        tasks_total=total,
        avg_response_ms=int(row.avg_ms) if row.avg_ms else None,
        success_rate=round((row.success_count or 0) / total, 3) if total > 0 else None,
        last_active=row.last_active,
        manages=agent_meta.get("manages", []),
    )


@router.get("", response_model=AgentListResponse)
async def list_agents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all agents with live stats (single batch query)."""
    stats = await _batch_agent_stats(db)
    agents = []
    for i, meta in enumerate(AGENT_REGISTRY):
        s = stats.get(meta["name"], {})
        tasks_today = s.get("tasks_today", 0)
        agents.append(
            AgentInfo(
                id=f"agent-{i + 1:02d}",
                agent_key=meta.get("agent_key", meta["name"]),
                name=meta["name"],
                display_name=meta["display_name"],
                human_name=meta.get("human_name"),
                description=meta["description"],
                tier=meta.get("tier", 3),
                lane=meta["lane"],
                role=meta.get("role"),
                status="active" if tasks_today > 0 else "idle",
                tasks_today=tasks_today,
                tasks_total=s.get("tasks_total", 0),
                avg_response_ms=s.get("avg_response_ms"),
                success_rate=s.get("success_rate"),
                last_active=s.get("last_active"),
                manages=meta.get("manages", []),
            )
        )
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
        from app.services.event_service import route_direct
        from app.agents.agent_factory import AgentFactory
        from app.database import get_sync_session

        sync_db = get_sync_session()
        try:
            event_dict_sync = {
                **event_dict,
                "event_id": event_record.id,
                "customer_id": body.customer_id,
            }
            route_result = route_direct(sync_db, event_dict_sync)
            agent_result = route_result.get("result", {})

            # Post-processing
            routed_agent = route_result.get("agent_name")
            if agent_result.get("success") and body.customer_id:
                agent_inst = AgentFactory.create(routed_agent) if routed_agent and AgentFactory.is_registered(routed_agent) else None
                if agent_inst and routed_agent == "health_monitor" and hasattr(agent_inst, "save_score"):
                    agent_inst.save_score(sync_db, body.customer_id, agent_result)
                elif agent_inst and routed_agent == "troubleshooter" and hasattr(agent_inst, "save_result"):
                    ticket_id = event_dict.get("payload", {}).get("ticket_id")
                    if ticket_id:
                        agent_inst.save_result(sync_db, ticket_id, agent_result)
                elif agent_inst and routed_agent == "escalation_summary" and hasattr(agent_inst, "save_result"):
                    ticket_id = event_dict.get("payload", {}).get("ticket_id")
                    if ticket_id:
                        agent_inst.save_result(sync_db, ticket_id, agent_result)
                elif agent_inst and routed_agent == "qbr_value" and hasattr(agent_inst, "save_report"):
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
                "routed_to": routed_agent,
                "customer": str(body.customer_id) if body.customer_id else None,
                "status": "completed" if agent_result.get("success") else "failed",
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
