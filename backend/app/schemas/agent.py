from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AgentInfo(BaseModel):
    name: str
    display_name: str
    description: str
    lane: str
    status: str = "idle"
    current_task: str | None = None
    tasks_today: int = 0
    tasks_total: int = 0
    avg_response_ms: int | None = None
    success_rate: float | None = None
    last_active: datetime | None = None


class AgentListResponse(BaseModel):
    agents: list[AgentInfo]


class AgentLogItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    agent_name: str
    event_type: str | None = None
    trigger_event: str | None = None
    customer_name: str | None = None
    input_summary: str | None = None
    output_summary: str | None = None
    reasoning_summary: str | None = None
    status: str | None = None
    duration_ms: int | None = None
    created_at: datetime | None = None


class AgentLogResponse(BaseModel):
    logs: list[AgentLogItem]
    total: int
    limit: int
    offset: int


class OrchestrationFlowItem(BaseModel):
    event_id: UUID
    event_type: str
    source: str | None = None
    customer_name: str | None = None
    routed_to: str | None = None
    status: str | None = None
    created_at: datetime | None = None
    processed_at: datetime | None = None


class OrchestrationFlowResponse(BaseModel):
    flows: list[OrchestrationFlowItem]


class AgentTriggerRequest(BaseModel):
    customer_id: UUID
    context: str | None = None


class AgentTriggerResponse(BaseModel):
    task_id: str
    message: str
    status: str
