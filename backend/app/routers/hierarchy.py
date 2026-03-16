"""
Hierarchy Router — API endpoints for the 4-tier agent hierarchy.

Prefix: /api/v2/hierarchy
Serves agent profiles from YAML config, enriched with live stats from the DB.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.profile_loader import ProfileLoader
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.agent_log import AgentLog
from app.models.user import User
from app.schemas.hierarchy import (
    AgentListV2Response,
    AgentProfileResponse,
    HierarchyResponse,
    HierarchyTier,
    LaneInfo,
    WorkflowDefinition,
    WorkflowListResponse,
    WorkflowStep,
)

router = APIRouter(prefix="/api/v2/hierarchy", tags=["hierarchy"])

TIER_NAMES = {1: "Supervisor", 2: "Lane Lead", 3: "Specialist", 4: "Foundation"}


async def _batch_agent_stats(db: AsyncSession) -> dict:
    """Fetch all agent stats in a single query (matching agents.py pattern)."""
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    result = await db.execute(
        select(
            AgentLog.agent_name,
            func.count().label("tasks_total"),
            func.count().filter(AgentLog.created_at >= today).label("tasks_today"),
            func.avg(AgentLog.duration_ms).filter(AgentLog.duration_ms.isnot(None)).label("avg_ms"),
            func.max(AgentLog.created_at).label("last_active"),
        ).group_by(AgentLog.agent_name)
    )
    rows = result.all()

    stats = {}
    for row in rows:
        stats[row.agent_name] = {
            "tasks_today": row.tasks_today or 0,
            "tasks_total": row.tasks_total or 0,
            "avg_response_ms": int(row.avg_ms) if row.avg_ms else None,
            "last_active": row.last_active,
        }
    return stats


def _build_agent_profile(agent_id: str, profile: dict, stats: dict) -> AgentProfileResponse:
    """Build an AgentProfileResponse from YAML profile + live DB stats."""
    s = stats.get(agent_id, {})
    tasks_today = s.get("tasks_today", 0)

    human_name = profile.get("name", agent_id)
    return AgentProfileResponse(
        id=agent_id,
        agent_key=agent_id,
        name=human_name,
        human_name=human_name,
        display_name=profile.get("codename") or profile.get("role", agent_id),
        codename=profile.get("codename"),
        tier=profile.get("tier", 3),
        lane=profile.get("lane"),
        role=profile.get("role", ""),
        personality=profile.get("personality"),
        traits=profile.get("traits", []),
        tools=profile.get("tools", []),
        expertise=profile.get("expertise", []),
        quirks=profile.get("quirks", []),
        reports_to=profile.get("reports_to"),
        manages=profile.get("manages", []),
        status="active" if tasks_today > 0 else "idle",
        tasks_today=tasks_today,
        tasks_total=s.get("tasks_total", 0),
        avg_response_ms=s.get("avg_response_ms"),
        last_active=s.get("last_active"),
    )


@router.get("", response_model=HierarchyResponse)
async def get_hierarchy(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the full 4-tier organization hierarchy with live agent stats."""
    loader = ProfileLoader.get()
    stats = await _batch_agent_stats(db)

    # Build tiers
    tiers = []
    for tier_num in [1, 2, 3, 4]:
        agent_ids = loader.get_agents_in_tier(tier_num)
        agents = []
        for aid in agent_ids:
            profile = loader.get_agent_profile(aid)
            if profile:
                agents.append(_build_agent_profile(aid, profile, stats))
        tiers.append(HierarchyTier(
            tier=tier_num,
            name=TIER_NAMES.get(tier_num, f"Tier {tier_num}"),
            agents=agents,
        ))

    # Build lanes
    org = loader.get_org_structure()
    lanes_config = org.get("organization", {}).get("lanes", {})
    lanes = {}
    for lane_name, lane_data in lanes_config.items():
        lanes[lane_name] = LaneInfo(
            lead=lane_data.get("lead", ""),
            specialists=lane_data.get("specialists", []),
        )

    return HierarchyResponse(
        organization=org.get("organization", {}).get("name", "HivePro CS Control Plane"),
        tiers=tiers,
        lanes=lanes,
    )


@router.get("/agents", response_model=AgentListV2Response)
async def list_agents_v2(
    tier: int | None = Query(default=None, ge=1, le=4, description="Filter by tier"),
    lane: str | None = Query(default=None, description="Filter by lane: support, value, delivery"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all agents with YAML profiles and live stats."""
    loader = ProfileLoader.get()
    stats = await _batch_agent_stats(db)

    agents = []
    for agent_id in loader.get_agent_ids():
        profile = loader.get_agent_profile(agent_id)
        if not profile:
            continue
        if tier is not None and profile.get("tier") != tier:
            continue
        if lane is not None and profile.get("lane") != lane:
            continue
        agents.append(_build_agent_profile(agent_id, profile, stats))

    return AgentListV2Response(agents=agents, total=len(agents))


@router.get("/agents/{agent_id}", response_model=AgentProfileResponse)
async def get_agent_v2(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single agent's profile with live stats."""
    loader = ProfileLoader.get()
    profile = loader.get_agent_profile(agent_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

    stats = await _batch_agent_stats(db)
    return _build_agent_profile(agent_id, profile, stats)


@router.get("/workflows", response_model=WorkflowListResponse)
async def list_workflows(
    current_user: User = Depends(get_current_user),
):
    """List all workflow definitions from YAML config."""
    loader = ProfileLoader.get()
    raw_workflows = loader.get_all_workflows()

    workflows = []
    for name, wf in raw_workflows.items():
        steps = []
        for step in wf.get("steps", []):
            steps.append(WorkflowStep(
                agent=step.get("agent", ""),
                action=step.get("action", ""),
                condition=step.get("condition"),
            ))
        workflows.append(WorkflowDefinition(
            name=name,
            description=wf.get("description", ""),
            trigger_events=wf.get("trigger_events", []),
            steps=steps,
        ))

    return WorkflowListResponse(workflows=workflows)
