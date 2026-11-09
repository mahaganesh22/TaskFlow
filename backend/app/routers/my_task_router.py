
from uuid import UUID
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.dependencies import get_current_user

from app.models import User

from app.schemas.task_schema import TaskListResponse
from app.services import task_service


router = APIRouter(
    prefix="/api/tasks",
    tags=["My Tasks"]
)


@router.get(
    "/assigned-to-me",
    response_model=TaskListResponse
)
def get_assigned_tasks(
    status: Literal["TODO", "IN_PROGRESS", "DONE"] | None = None,

    priority: Literal["LOW", "MEDIUM", "HIGH"] | None = None,

    limit: int = Query(default=20, ge=1, le=100),

    offset: int = Query(default=0, ge=0),

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user)
):
    return task_service.get_assigned_tasks(
        db=db,
        current_user=current_user,
        status=status,
        priority=priority,
        limit=limit,
        offset=offset
    )
