from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ToolCallEntry(BaseModel):
    tool_name: str
    arguments: dict = {}
    result_preview: str | None = None
    duration_ms: int | None = None


class ExecutionRoundResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    stage_number: int
    stage_name: str
    stage_type: str
    input_summary: str | None = None
    output_summary: str | None = None
    tools_called: list[ToolCallEntry] = []
    duration_ms: int | None = None
    tokens_used: int | None = None
    status: str
    metadata: dict = {}


class ExecutionSummary(BaseModel):
    execution_id: UUID
    agent_id: str
    agent_name: str
    tier: int
    lane: str | None = None
    event_id: UUID | None = None
    event_type: str | None = None
    customer_name: str | None = None
    pipeline_type: str
    status: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    total_duration_ms: int | None = None
    total_tokens: int | None = None
    confidence: float | None = None
    current_stage: str | None = None
    stages_completed: int = 0
    stages_total: int = 0
    rounds: list[ExecutionRoundResponse] = []


class ActivePipelinesResponse(BaseModel):
    executions: list[ExecutionSummary]


class ExecutionRoundsResponse(BaseModel):
    execution_id: UUID
    rounds: list[ExecutionRoundResponse]
    total: int
    limit: int
    offset: int


class AgentExecutionSummary(BaseModel):
    execution_id: UUID
    event_type: str | None = None
    customer_name: str | None = None
    status: str
    total_duration_ms: int | None = None
    confidence: float | None = None
    stages_completed: int = 0
    started_at: datetime | None = None


class AgentExecutionsResponse(BaseModel):
    agent_id: str
    agent_name: str
    executions: list[AgentExecutionSummary]
    total: int
    limit: int
    offset: int


class RecentExecutionSummary(BaseModel):
    execution_id: UUID
    agent_id: str
    agent_name: str
    tier: int
    lane: str | None = None
    event_type: str | None = None
    customer_name: str | None = None
    pipeline_type: str
    status: str
    total_duration_ms: int | None = None
    total_tokens: int | None = None
    confidence: float | None = None
    stages_completed: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None


class RecentExecutionsResponse(BaseModel):
    executions: list[RecentExecutionSummary]
    total: int
    limit: int
    offset: int
