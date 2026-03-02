from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.user import CsOwnerBrief


class ActionItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None = None
    source_type: str | None = None
    source_id: UUID | None = None
    owner: CsOwnerBrief | None = None
    deadline: datetime | None = None
    status: str = "pending"
    created_at: datetime
