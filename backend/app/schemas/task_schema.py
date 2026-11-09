from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator


class TaskResponse(BaseModel):
    id: UUID
    title: str
    description: str | None
    status: Literal["TODO", "IN_PROGRESS", "DONE"]
    priority: Literal["LOW", "MEDIUM", "HIGH"]
    due_date: datetime | None
    project_id: UUID
    created_by: UUID
    assignee_id: UUID | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)



class TaskCreateRequest(BaseModel):

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)

    description: str | None = None

    priority: Literal["LOW", "MEDIUM", "HIGH"] = "MEDIUM"

    due_date: datetime | None = None

    assignee_id: UUID | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:

        value = value.strip()

        if not value:
            raise ValueError("Task title cannot be empty")

        return value

    @field_validator("due_date")
    @classmethod
    def validate_due_date_timezone(
        cls,
        value: datetime | None
    ) -> datetime | None:

        if value is not None:
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError("Due date must include a timezone")

        return value



class TaskUpdateRequest(BaseModel):

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, max_length=200)

    description: str | None = None

    priority: Literal["LOW", "MEDIUM", "HIGH"] | None = None

    due_date: datetime | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value):

        if value is not None:
            value = value.strip()

            if not value:
                raise ValueError("Task title cannot be empty")

        return value

    @field_validator("due_date")
    @classmethod
    def validate_due_date_timezone(cls, value):

        if value is not None:
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError("Due date must include a timezone")

        return value




class TaskAssignmentRequest(BaseModel):

    model_config = ConfigDict(extra="forbid")

    assignee_id: UUID




class TaskStatusUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["TODO", "IN_PROGRESS", "DONE"]


class TaskListResponse(BaseModel):
    items: list[TaskResponse]
    total: int
    limit: int
    offset: int