"""
Pipeline Service — async query layer for agent_execution_rounds.

Provides methods to list, filter, and aggregate pipeline execution data
for the /api/v2/pipeline router.
"""

import logging
from uuid import UUID

from sqlalchemy import case, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_execution_round import AgentExecutionRound
from app.models.customer import Customer
from app.models.event import Event

logger = logging.getLogger("services.pipeline")

# Tier → pipeline_type label
TIER_PIPELINE_TYPE = {
    1: "tier_1_supervisor",
    2: "tier_2_lane_lead",
    3: "tier_3_specialist",
    4: "tier_4_foundation",
}


class PipelineService:

    async def get_active_executions(self, db: AsyncSession) -> list[dict]:
        """Get executions that have at least one round with status='running'."""
        # Find distinct execution_ids with running status
        running_ids_q = (
            select(distinct(AgentExecutionRound.execution_id))
            .where(AgentExecutionRound.status == "running")
        )
        running_result = await db.execute(running_ids_q)
        running_ids = [row[0] for row in running_result.all()]

        logger.info("[active] Found %d running execution_ids", len(running_ids))

        if not running_ids:
            return []

        summaries = []
        for eid in running_ids:
            summary = await self.get_execution_summary(db, eid)
            if summary:
                summaries.append(summary)
        return summaries

    async def get_execution_summary(self, db: AsyncSession, execution_id: UUID) -> dict | None:
        """Build a full execution summary from all rounds for an execution_id."""
        query = (
            select(AgentExecutionRound)
            .where(AgentExecutionRound.execution_id == execution_id)
            .order_by(AgentExecutionRound.stage_number)
        )
        result = await db.execute(query)
        rounds = result.scalars().all()

        logger.info("[summary] execution_id=%s  rounds_found=%d", execution_id, len(rounds))

        if not rounds:
            return None

        first = rounds[0]

        # Resolve customer_name + event_type through event
        customer_name = None
        event_type = None
        if first.event_id:
            event_q = (
                select(Event.event_type, Customer.name)
                .outerjoin(Customer, Event.customer_id == Customer.id)
                .where(Event.id == first.event_id)
            )
            event_result = await db.execute(event_q)
            event_row = event_result.first()
            if event_row:
                event_type = event_row[0]
                customer_name = event_row[1]

        # Derive aggregate fields
        started_at = min((r.created_at for r in rounds if r.created_at), default=None)
        completed_at = max((r.created_at for r in rounds if r.created_at), default=None)
        total_duration_ms = sum(r.duration_ms or 0 for r in rounds)
        total_tokens = sum(r.tokens_used or 0 for r in rounds)
        stages_completed = sum(1 for r in rounds if r.status == "completed")
        stages_total = len(rounds)

        # Status: running if any running, failed if any failed and none running, else completed
        statuses = {r.status for r in rounds}
        if "running" in statuses:
            status = "running"
            current_stage = next((r.stage_name for r in rounds if r.status == "running"), None)
        elif "failed" in statuses:
            status = "failed"
            current_stage = None
        else:
            status = "completed"
            current_stage = None
            completed_at = max((r.created_at for r in rounds if r.created_at), default=None)

        # Confidence from reflect stage
        confidence = None
        for r in rounds:
            if r.confidence is not None:
                confidence = r.confidence

        round_dicts = [_format_round(r) for r in rounds]

        return {
            "execution_id": execution_id,
            "agent_id": first.agent_id,
            "agent_name": first.agent_name or first.agent_id,
            "tier": first.tier,
            "lane": first.lane,
            "event_id": first.event_id,
            "event_type": event_type,
            "customer_name": customer_name,
            "pipeline_type": TIER_PIPELINE_TYPE.get(first.tier, "unknown"),
            "status": status,
            "started_at": started_at,
            "completed_at": completed_at if status != "running" else None,
            "total_duration_ms": total_duration_ms,
            "total_tokens": total_tokens or None,
            "confidence": confidence,
            "current_stage": current_stage,
            "stages_completed": stages_completed,
            "stages_total": stages_total,
            "rounds": round_dicts,
        }

    async def get_execution_rounds(
        self, db: AsyncSession, execution_id: UUID, limit: int = 20, offset: int = 0
    ) -> tuple[list[dict], int]:
        """Get paginated rounds for an execution."""
        # Total count
        count_q = (
            select(func.count())
            .select_from(AgentExecutionRound)
            .where(AgentExecutionRound.execution_id == execution_id)
        )
        total = (await db.execute(count_q)).scalar() or 0

        # Paginated rows
        query = (
            select(AgentExecutionRound)
            .where(AgentExecutionRound.execution_id == execution_id)
            .order_by(AgentExecutionRound.stage_number)
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(query)
        rounds = [_format_round(r) for r in result.scalars().all()]

        return rounds, total

    async def get_agent_executions(
        self, db: AsyncSession, agent_id: str, limit: int = 10, offset: int = 0
    ) -> tuple[list[dict], int]:
        """Get recent execution summaries for a specific agent."""
        # Count distinct executions
        count_q = (
            select(func.count(distinct(AgentExecutionRound.execution_id)))
            .where(AgentExecutionRound.agent_id == agent_id)
        )
        total = (await db.execute(count_q)).scalar() or 0

        # Get distinct execution_ids, most recent first
        exec_ids_q = (
            select(
                AgentExecutionRound.execution_id,
                func.min(AgentExecutionRound.created_at).label("started_at"),
                func.max(AgentExecutionRound.created_at).label("completed_at"),
                func.sum(AgentExecutionRound.duration_ms).label("total_duration_ms"),
                func.count().label("stages_completed"),
                func.max(AgentExecutionRound.confidence).label("confidence"),
                func.max(
                    case(
                        (AgentExecutionRound.status == "running", "running"),
                        (AgentExecutionRound.status == "failed", "failed"),
                        else_="completed",
                    )
                ).label("status"),
                AgentExecutionRound.event_id,
            )
            .where(AgentExecutionRound.agent_id == agent_id)
            .group_by(AgentExecutionRound.execution_id, AgentExecutionRound.event_id)
            .order_by(func.max(AgentExecutionRound.created_at).desc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(exec_ids_q)
        rows = result.all()

        # Batch resolve event_type + customer_name
        event_ids = {r.event_id for r in rows if r.event_id}
        event_info = {}
        if event_ids:
            ev_q = (
                select(Event.id, Event.event_type, Customer.name)
                .outerjoin(Customer, Event.customer_id == Customer.id)
                .where(Event.id.in_(event_ids))
            )
            ev_result = await db.execute(ev_q)
            for ev_row in ev_result.all():
                event_info[ev_row[0]] = {
                    "event_type": ev_row[1],
                    "customer_name": ev_row[2],
                }

        executions = []
        for r in rows:
            info = event_info.get(r.event_id, {})
            executions.append({
                "execution_id": r.execution_id,
                "event_type": info.get("event_type"),
                "customer_name": info.get("customer_name"),
                "status": r.status or "completed",
                "total_duration_ms": r.total_duration_ms,
                "confidence": r.confidence,
                "stages_completed": r.stages_completed or 0,
                "started_at": r.started_at,
            })

        return executions, total

    async def get_recent_executions(
        self, db: AsyncSession, limit: int = 20, offset: int = 0
    ) -> tuple[list[dict], int]:
        """Get recent execution summaries across ALL agents, most recent first."""
        count_q = select(func.count(distinct(AgentExecutionRound.execution_id)))
        total = (await db.execute(count_q)).scalar() or 0

        logger.info("[recent] Total distinct executions in DB: %d  (limit=%d, offset=%d)", total, limit, offset)

        exec_ids_q = (
            select(
                AgentExecutionRound.execution_id,
                AgentExecutionRound.agent_id,
                AgentExecutionRound.agent_name,
                AgentExecutionRound.tier,
                AgentExecutionRound.lane,
                func.min(AgentExecutionRound.created_at).label("started_at"),
                func.max(AgentExecutionRound.created_at).label("completed_at"),
                func.sum(AgentExecutionRound.duration_ms).label("total_duration_ms"),
                func.sum(AgentExecutionRound.tokens_used).label("total_tokens"),
                func.count().label("stages_completed"),
                func.max(AgentExecutionRound.confidence).label("confidence"),
                func.max(
                    case(
                        (AgentExecutionRound.status == "running", "running"),
                        (AgentExecutionRound.status == "failed", "failed"),
                        else_="completed",
                    )
                ).label("status"),
                AgentExecutionRound.event_id,
            )
            .group_by(
                AgentExecutionRound.execution_id,
                AgentExecutionRound.event_id,
                AgentExecutionRound.agent_id,
                AgentExecutionRound.agent_name,
                AgentExecutionRound.tier,
                AgentExecutionRound.lane,
            )
            .order_by(func.max(AgentExecutionRound.created_at).desc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(exec_ids_q)
        rows = result.all()

        logger.info("[recent] Query returned %d rows", len(rows))

        event_ids = {r.event_id for r in rows if r.event_id}
        event_info: dict = {}
        if event_ids:
            ev_q = (
                select(Event.id, Event.event_type, Customer.name)
                .outerjoin(Customer, Event.customer_id == Customer.id)
                .where(Event.id.in_(event_ids))
            )
            ev_result = await db.execute(ev_q)
            for ev_row in ev_result.all():
                event_info[ev_row[0]] = {
                    "event_type": ev_row[1],
                    "customer_name": ev_row[2],
                }

        executions = []
        for r in rows:
            info = event_info.get(r.event_id, {})
            executions.append({
                "execution_id": r.execution_id,
                "agent_id": r.agent_id,
                "agent_name": r.agent_name or r.agent_id,
                "tier": r.tier,
                "lane": r.lane,
                "event_type": info.get("event_type"),
                "customer_name": info.get("customer_name"),
                "pipeline_type": TIER_PIPELINE_TYPE.get(r.tier, "unknown"),
                "status": r.status or "completed",
                "total_duration_ms": r.total_duration_ms,
                "total_tokens": r.total_tokens or None,
                "confidence": r.confidence,
                "stages_completed": r.stages_completed or 0,
                "started_at": r.started_at,
                "completed_at": r.completed_at if (r.status or "completed") != "running" else None,
            })

        if executions:
            logger.info("[recent] Returning %d executions: %s",
                        len(executions),
                        [f"{e['agent_name']}({e['status']})" for e in executions[:5]])

        return executions, total


def _format_round(r: AgentExecutionRound) -> dict:
    """Convert an ORM round to a dict matching ExecutionRoundResponse."""
    tools = r.tools_called or []
    tool_entries = []
    for t in tools:
        if isinstance(t, dict):
            tool_entries.append({
                "tool_name": t.get("tool_name", "unknown"),
                "arguments": t.get("arguments", {}),
                "result_preview": t.get("result_preview"),
                "duration_ms": t.get("duration_ms"),
            })

    return {
        "stage_number": r.stage_number,
        "stage_name": r.stage_name,
        "stage_type": r.stage_type,
        "input_summary": r.input_summary,
        "output_summary": r.output_summary,
        "tools_called": tool_entries,
        "duration_ms": r.duration_ms,
        "tokens_used": r.tokens_used,
        "status": r.status,
        "metadata": r.metadata_ or {},
    }


pipeline_service = PipelineService()
