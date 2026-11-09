
from uuid import UUID
from typing import Literal

from fastapi import APIRouter, Depends, status, Response, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.dependencies import get_current_user

from app.models import User

from app.services import task_service

from app.schemas.task_schema import (
    TaskCreateRequest,
    TaskResponse,
    TaskListResponse,
    TaskUpdateRequest,
    TaskAssignmentRequest,
    TaskStatusUpdateRequest
)


router = APIRouter(
    prefix="/api/projects/{project_id}/tasks",
    tags=["Tasks"]
)

@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED
)
def create_task(
    project_id: UUID,
    task_data: TaskCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return task_service.create_task(
        db,
        project_id,
        current_user,
        task_data
    )



@router.get(
    "",
    response_model=TaskListResponse
)
def get_project_tasks(
    project_id: UUID,

    priority: Literal["LOW", "MEDIUM", "HIGH"] | None = None,
    assignee_id: UUID | None = None,
    search: str | None = Query(default=None, max_length=100),

    sort_by: Literal["priority", "due_date", "created_at"] = "created_at",
    sort_order: Literal["asc", "desc"] = "desc",

    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),

    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return task_service.get_project_tasks(
        db=db,
        project_id=project_id,
        current_user=current_user,
        priority=priority,
        assignee_id=assignee_id,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset
    )



# GET a single task
@router.get(
    "/{task_id}",
    response_model=TaskResponse
)
def get_task(
    project_id: UUID,
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return task_service.get_task_by_id(
        db, project_id, task_id, current_user
    )


# UPDATE task details
@router.patch(
    "/{task_id}",
    response_model=TaskResponse
)
def update_task(
    project_id: UUID,
    task_id: UUID,
    task_data: TaskUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return task_service.update_task_details(
        db, project_id, task_id, current_user, task_data
    )


# ASSIGN task
@router.patch(
    "/{task_id}/assignee",
    response_model=TaskResponse
)
def assign_task(
    project_id: UUID,
    task_id: UUID,
    assignment_data: TaskAssignmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return task_service.assign_task(
        db, project_id, task_id, current_user, assignment_data
    )


# UPDATE task status
@router.patch(
    "/{task_id}/status",
    response_model=TaskResponse
)
def update_task_status(
    project_id: UUID,
    task_id: UUID,
    status_data: TaskStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return task_service.update_task_status(
        db, project_id, task_id, current_user, status_data
    )


# DELETE task
@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response
)
def delete_task(
    project_id: UUID,
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task_service.delete_task(
        db, project_id, task_id, current_user
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)

