from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.user import CsOwnerBrief


class CustomerListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    industry: str | None = None
    tier: str | None = None
    health_score: int | None = None
    risk_level: str | None = None
    risk_count: int = 0
    open_ticket_count: int = 0
    cs_owner: CsOwnerBrief | None = None
    renewal_date: date | None = None
    days_to_renewal: int | None = None
    last_call_date: date | None = None
    primary_contact_name: str | None = None


class CustomerListResponse(BaseModel):
    customers: list[CustomerListItem]
    total: int
    limit: int
    offset: int


class DeploymentInfo(BaseModel):
    mode: str | None = None
    product_version: str | None = None
    integrations: list[str] = []
    known_constraints: list[str] = []


class HealthInfo(BaseModel):
    current_score: int | None = None
    risk_level: str | None = None
    risk_flags: list[str] = []
    factors: dict = {}


class CustomerDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    industry: str | None = None
    tier: str | None = None
    contract_start: date | None = None
    renewal_date: date | None = None
    days_to_renewal: int | None = None
    primary_contact_name: str | None = None
    primary_contact_email: str | None = None
    cs_owner: CsOwnerBrief | None = None
    deployment: DeploymentInfo
    health: HealthInfo
    open_ticket_count: int = 0
    recent_call_count: int = 0
    pending_action_items: int = 0
    metadata: dict = {}
    created_at: datetime
    updated_at: datetime


class CustomerCreate(BaseModel):
    name: str
    industry: str | None = None
    tier: str | None = None
    contract_start: date | None = None
    renewal_date: date | None = None
    primary_contact_name: str | None = None
    primary_contact_email: str | None = None
    cs_owner_id: UUID | None = None
    deployment_mode: str = "OVA"
    product_version: str | None = None
    integrations: list[str] = []
    known_constraints: list[str] = []


class CustomerUpdate(BaseModel):
    name: str | None = None
    industry: str | None = None
    tier: str | None = None
    contract_start: date | None = None
    renewal_date: date | None = None
    primary_contact_name: str | None = None
    primary_contact_email: str | None = None
    cs_owner_id: UUID | None = None
    deployment_mode: str | None = None
    product_version: str | None = None
    integrations: list[str] | None = None
    known_constraints: list[str] | None = None
