from pydantic import BaseModel, EmailStr, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Literal

from app.schemas.auth_schema import UserPublicResponse


class ProjectMemberInviteRequest(BaseModel):
    email: EmailStr

    model_config = ConfigDict(extra="forbid")


class ProjectMemberResponse(BaseModel):
    id: UUID
    project_id: UUID
    user_id: UUID
    role: Literal["OWNER", "MEMBER"]
    joined_at: datetime
    user: UserPublicResponse

    model_config = ConfigDict(from_attributes=True)