from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ActivityResponse(BaseModel):
    id: UUID
    project_id: UUID
    actor_id: UUID
    actor_name: str
    task_id: UUID | None
    task_title: str | None
    activity_type: str
    details: dict | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
