"""
Workflows Router — API endpoints for workflow definitions and active instances.

Prefix: /api/v2/workflows

Workflow instances map 1:1 to events (event.id = instance_id).
Status is derived from events + agent_execution_rounds tables.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.profile_loader import ProfileLoader
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.agent_execution_round import AgentExecutionRound
from app.models.customer import Customer
from app.models.event import Event
from app.models.user import User
from app.schemas.hierarchy import (
    ActiveWorkflowsResponse,
    WorkflowDefinition,
    WorkflowInstanceStatus,
    WorkflowInstanceSummary,
    WorkflowListResponse,
    WorkflowStep,
    WorkflowStepStatus,
)

logger = logging.getLogger("routers.workflows")

router = APIRouter(prefix="/api/v2/workflows", tags=["workflows"])


# ── Workflow Definitions ────────────────────────────────────────


@router.get("/", response_model=WorkflowListResponse)
async def list_workflows(
    current_user: User = Depends(get_current_user),
):
    """Get all workflow definitions from YAML configuration."""
    loader = ProfileLoader.get()
    raw = loader.get_all_workflows()

    workflows = []
    for name, wf in raw.items():
        steps = []
        for s in wf.get("steps", []):
            steps.append(WorkflowStep(
                agent=s.get("agent", ""),
                action=s.get("action", ""),
                condition=s.get("condition"),
            ))
        workflows.append(WorkflowDefinition(
            name=name,
            description=wf.get("description", ""),
            trigger_events=wf.get("trigger_events", []),
            steps=steps,
        ))

    return WorkflowListResponse(workflows=workflows)


# ── Active Workflow Instances ───────────────────────────────────


@router.get("/active", response_model=ActiveWorkflowsResponse)
async def get_active_workflows(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get currently running workflow instances (events being processed)."""
    loader = ProfileLoader.get()

    # Find events that are processing or queued
    query = (
        select(Event, Customer.name.label("customer_name"))
        .outerjoin(Customer, Event.customer_id == Customer.id)
        .where(Event.status.in_(["processing", "queued", "pending"]))
        .order_by(Event.created_at.desc())
        .limit(50)
    )
    result = await db.execute(query)
    rows = result.all()

    instances = []
    for row in rows:
        event = row[0]
        customer_name = row[1]

        # Find matching workflow definition
        wf = loader.get_workflow_for_event(event.event_type)
        if not wf:
            continue

        workflow_name = wf.get("name", "unknown")
        total_steps = len(wf.get("steps", []))

        # Find current progress from execution rounds
        rounds_q = (
            select(
                AgentExecutionRound.agent_id,
                AgentExecutionRound.status,
            )
            .where(AgentExecutionRound.event_id == event.id)
            .order_by(AgentExecutionRound.stage_number)
        )
        rounds_result = await db.execute(rounds_q)
        rounds = rounds_result.all()

        # Derive current step and agent
        completed_agents = set()
        current_agent = None
        for r in rounds:
            if r.status == "completed":
                completed_agents.add(r.agent_id)
            elif r.status == "running":
                current_agent = r.agent_id

        current_step = len(completed_agents)

        instances.append(WorkflowInstanceSummary(
            instance_id=str(event.id),
            workflow_name=workflow_name,
            event_id=str(event.id),
            customer_name=customer_name,
            current_step=current_step,
            total_steps=total_steps,
            current_agent=current_agent,
            status="running" if current_agent else "queued",
            started_at=event.created_at,
        ))

    return ActiveWorkflowsResponse(instances=instances)


# ── Workflow Instance Status ────────────────────────────────────


@router.get("/{instance_id}/status", response_model=WorkflowInstanceStatus)
async def get_workflow_status(
    instance_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed status for a specific workflow instance (event)."""
    # Fetch the event
    event_q = (
        select(Event, Customer.name.label("customer_name"))
        .outerjoin(Customer, Event.customer_id == Customer.id)
        .where(Event.id == instance_id)
    )
    event_result = await db.execute(event_q)
    row = event_result.first()

    if not row:
        raise HTTPException(status_code=404, detail="Workflow instance not found")

    event = row[0]
    customer_name = row[1]

    # Find matching workflow definition
    loader = ProfileLoader.get()
    wf = loader.get_workflow_for_event(event.event_type)
    if not wf:
        raise HTTPException(
            status_code=404,
            detail=f"No workflow defined for event type '{event.event_type}'",
        )

    workflow_name = wf.get("name", "unknown")
    wf_steps = wf.get("steps", [])

    # Get all execution rounds for this event
    rounds_q = (
        select(AgentExecutionRound)
        .where(AgentExecutionRound.event_id == instance_id)
        .order_by(AgentExecutionRound.created_at)
    )
    rounds_result = await db.execute(rounds_q)
    rounds = rounds_result.scalars().all()

    # Index rounds by agent_id for lookup
    agent_rounds: dict[str, list] = {}
    for r in rounds:
        agent_rounds.setdefault(r.agent_id, []).append(r)

    # Resolve agent names
    profiles = loader.get_all_profiles()

    # Map workflow steps to execution data
    steps: list[WorkflowStepStatus] = []
    overall_status = "completed"
    total_duration_ms = 0

    for i, step_def in enumerate(wf_steps):
        agent_id = step_def.get("agent", "")
        condition = step_def.get("condition")
        agent_name = profiles.get(agent_id, {}).get("name", agent_id)

        agent_execs = agent_rounds.get(agent_id, [])

        if agent_execs:
            # Agent has execution data
            statuses = {r.status for r in agent_execs}
            step_duration = sum(r.duration_ms or 0 for r in agent_execs)
            total_duration_ms += step_duration

            if "running" in statuses:
                step_status = "running"
                overall_status = "running"
            elif "failed" in statuses:
                step_status = "failed"
                if overall_status != "running":
                    overall_status = "failed"
            else:
                step_status = "completed"

            steps.append(WorkflowStepStatus(
                step=i + 1,
                agent=agent_id,
                agent_name=agent_name,
                status=step_status,
                duration_ms=step_duration if step_duration > 0 else None,
                condition=condition,
            ))
        else:
            # No execution data — pending or skipped
            step_status = "skipped" if condition and event.status == "completed" else "pending"
            if step_status == "pending" and overall_status == "completed":
                overall_status = "running"  # Still has pending steps

            steps.append(WorkflowStepStatus(
                step=i + 1,
                agent=agent_id,
                agent_name=agent_name,
                status=step_status,
                condition=condition,
            ))

    # Derive overall timing
    started_at = event.created_at
    completed_at = event.processed_at if overall_status == "completed" else None

    return WorkflowInstanceStatus(
        instance_id=str(instance_id),
        workflow_name=workflow_name,
        event_id=str(event.id),
        customer_name=customer_name,
        status=overall_status,
        started_at=started_at,
        completed_at=completed_at,
        total_duration_ms=total_duration_ms if total_duration_ms > 0 else None,
        steps=steps,
    )
