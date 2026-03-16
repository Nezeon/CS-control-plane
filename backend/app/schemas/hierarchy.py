from datetime import datetime

from pydantic import BaseModel


class AgentProfileResponse(BaseModel):
    id: str
    agent_key: str = ""  # Same as id — for frontend compatibility
    name: str
    human_name: str = ""  # Same as name — for frontend compatibility
    display_name: str = ""  # codename or role — for frontend compatibility
    codename: str | None = None
    tier: int
    lane: str | None = None
    role: str
    personality: str | None = None
    traits: list[str] = []
    tools: list[str] = []
    expertise: list[str] = []
    quirks: list[str] = []
    reports_to: str | None = None
    manages: list[str] = []
    status: str = "idle"
    tasks_today: int = 0
    tasks_total: int = 0
    avg_response_ms: int | None = None
    last_active: datetime | None = None


class HierarchyTier(BaseModel):
    tier: int
    name: str
    agents: list[AgentProfileResponse]


class LaneInfo(BaseModel):
    lead: str
    specialists: list[str]


class HierarchyResponse(BaseModel):
    organization: str
    tiers: list[HierarchyTier]
    lanes: dict[str, LaneInfo]


class AgentListV2Response(BaseModel):
    agents: list[AgentProfileResponse]
    total: int


class WorkflowStep(BaseModel):
    agent: str
    action: str
    condition: str | None = None


class WorkflowDefinition(BaseModel):
    name: str
    description: str
    trigger_events: list[str]
    steps: list[WorkflowStep]


class WorkflowListResponse(BaseModel):
    workflows: list[WorkflowDefinition]


class WorkflowInstanceSummary(BaseModel):
    instance_id: str
    workflow_name: str
    event_id: str | None = None
    customer_name: str | None = None
    current_step: int = 0
    total_steps: int = 0
    current_agent: str | None = None
    status: str = "running"
    started_at: datetime | None = None


class ActiveWorkflowsResponse(BaseModel):
    instances: list[WorkflowInstanceSummary]


class WorkflowStepStatus(BaseModel):
    step: int
    agent: str
    agent_name: str | None = None
    status: str
    duration_ms: int | None = None
    condition: str | None = None


class WorkflowInstanceStatus(BaseModel):
    instance_id: str
    workflow_name: str
    event_id: str | None = None
    customer_name: str | None = None
    status: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    total_duration_ms: int | None = None
    steps: list[WorkflowStepStatus] = []
