from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from uuid import UUID
from datetime import datetime



class TransferOwnershipRequest(BaseModel):
    new_owner_id: UUID


class ProjectCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=1000)
    tech_stack: str | None = Field(default=None, max_length=1000)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Project name cannot be empty")

        return value


class ProjectUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=1000)
    tech_stack: str | None = Field(default=None, max_length=1000)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return value

        value = value.strip()

        if not value:
            raise ValueError("Project name cannot be empty")

        return value


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    tech_stack: str | None
    owner_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
