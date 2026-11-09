
from uuid import UUID
from typing import Literal

from fastapi import APIRouter, Depends, status, Response, Query, BackgroundTasks
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

from app.core.websocket_manager import manager

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
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = task_service.create_task(
        db,
        project_id,
        current_user,
        task_data
    )

    background_tasks.add_task(
        manager.broadcast_to_project,
        project_id,
        {
            "type": "TASK_CREATED",
            "project_id": str(project_id),
            "task_id": str(task.id)
        }
    )

    if task.assignee_id:
        background_tasks.add_task(
            manager.send_to_user,
            task.assignee_id,
            {
                "type": "ASSIGNED_TASKS_CHANGED",
                "project_id": str(project_id),
                "task_id": str(task.id)
            }
        )

    return task



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
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = task_service.update_task_details(
        db,
        project_id,
        task_id,
        current_user,
        task_data
    )

    background_tasks.add_task(
        manager.broadcast_to_project,
        project_id,
        {
            "type": "TASK_UPDATED",
            "project_id": str(project_id),
            "task_id": str(task.id)
        }
    )

    return task


# ASSIGN task
@router.patch(
    "/{task_id}/assignee",
    response_model=TaskResponse
)
def assign_task(
    project_id: UUID,
    task_id: UUID,
    assignment_data: TaskAssignmentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task, old_assignee_id = task_service.assign_task(
        db,
        project_id,
        task_id,
        current_user,
        assignment_data
    )

    background_tasks.add_task(
        manager.broadcast_to_project,
        project_id,
        {
            "type": "TASK_ASSIGNED",
            "project_id": str(project_id),
            "task_id": str(task.id),
            "assignee_id": str(task.assignee_id)
        }
    )

    affected_users = {
        user_id
        for user_id in (old_assignee_id, task.assignee_id)
        if user_id is not None
    }

    for user_id in affected_users:
        background_tasks.add_task(
            manager.send_to_user,
            user_id,
            {
                "type": "ASSIGNED_TASKS_CHANGED",
                "project_id": str(project_id),
                "task_id": str(task.id)
            }
        )

    return task


# UPDATE task status
@router.patch(
    "/{task_id}/status",
    response_model=TaskResponse
)
def update_task_status(
    project_id: UUID,
    task_id: UUID,
    status_data: TaskStatusUpdateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task, changed = task_service.update_task_status(
        db,
        project_id,
        task_id,
        current_user,
        status_data
    )

    if changed:
        background_tasks.add_task(
            manager.broadcast_to_project,
            project_id,
            {
                "type": "TASK_STATUS_CHANGED",
                "project_id": str(project_id),
                "task_id": str(task.id),
                "status": task.status
            }
        )

    return task


# DELETE task
@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response
)
def delete_task(
    project_id: UUID,
    task_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    assignee_id = task_service.delete_task(
        db,
        project_id,
        task_id,
        current_user
    )

    background_tasks.add_task(
        manager.broadcast_to_project,
        project_id,
        {
            "type": "TASK_DELETED",
            "project_id": str(project_id),
            "task_id": str(task_id)
        }
    )

    if assignee_id:
        background_tasks.add_task(
            manager.send_to_user,
            assignee_id,
            {
                "type": "ASSIGNED_TASKS_CHANGED",
                "project_id": str(project_id),
                "task_id": str(task_id)
            }
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)

