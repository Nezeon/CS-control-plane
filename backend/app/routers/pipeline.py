"""
Pipeline Router — API endpoints for pipeline execution traces.

Prefix: /api/v2/pipeline
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.profile_loader import ProfileLoader
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.pipeline import (
    ActivePipelinesResponse,
    AgentExecutionsResponse,
    AgentExecutionSummary,
    ExecutionRoundsResponse,
    ExecutionRoundResponse,
    ExecutionSummary,
    RecentExecutionsResponse,
    RecentExecutionSummary,
    ToolCallEntry,
)
from app.services.pipeline_service import pipeline_service

logger = logging.getLogger("routers.pipeline")

router = APIRouter(prefix="/api/v2/pipeline", tags=["pipeline"])


@router.get("/active", response_model=ActivePipelinesResponse)
async def get_active_pipelines(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get currently running pipeline executions."""
    summaries = await pipeline_service.get_active_executions(db)
    logger.info("GET /active → %d active executions", len(summaries))
    return ActivePipelinesResponse(
        executions=[ExecutionSummary(**s) for s in summaries]
    )


@router.get("/recent", response_model=RecentExecutionsResponse)
async def get_recent_executions(
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get recent pipeline executions across all agents, most recent first."""
    executions, total = await pipeline_service.get_recent_executions(db, limit, offset)
    logger.info("GET /recent → total=%d  returned=%d  (limit=%d, offset=%d)", total, len(executions), limit, offset)
    return RecentExecutionsResponse(
        executions=[RecentExecutionSummary(**e) for e in executions],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/agent/{agent_id}", response_model=AgentExecutionsResponse)
async def get_agent_executions(
    agent_id: str,
    limit: int = Query(default=10, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get recent pipeline executions for a specific agent."""
    loader = ProfileLoader.get()
    profile = loader.get_agent_profile(agent_id)
    agent_name = profile.get("name", agent_id) if profile else agent_id

    executions, total = await pipeline_service.get_agent_executions(db, agent_id, limit, offset)
    logger.info("GET /agent/%s → total=%d  returned=%d", agent_id, total, len(executions))

    return AgentExecutionsResponse(
        agent_id=agent_id,
        agent_name=agent_name,
        executions=[AgentExecutionSummary(**e) for e in executions],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{execution_id}", response_model=ExecutionSummary)
async def get_execution(
    execution_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get full pipeline execution with all rounds."""
    summary = await pipeline_service.get_execution_summary(db, execution_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Execution not found")

    return ExecutionSummary(**summary)


@router.get("/{execution_id}/rounds", response_model=ExecutionRoundsResponse)
async def get_execution_rounds(
    execution_id: UUID,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get paginated rounds for a pipeline execution."""
    rounds, total = await pipeline_service.get_execution_rounds(db, execution_id, limit, offset)

    return ExecutionRoundsResponse(
        execution_id=execution_id,
        rounds=[ExecutionRoundResponse(**r) for r in rounds],
        total=total,
        limit=limit,
        offset=offset,
    )
