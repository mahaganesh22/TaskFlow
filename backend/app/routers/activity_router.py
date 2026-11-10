from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.models import User
from app.schemas.activity_schema import ActivityResponse
from app.services import activity_service


router = APIRouter(
    prefix="/api/projects/{project_id}/activities",
    tags=["Activity"]
)


def _serialize_activity(activity) -> ActivityResponse:
    actor = activity.actor
    task = activity.task

    actor_name = "Deleted User"
    if actor is not None and actor.deleted_at is None:
        actor_name = actor.name

    return ActivityResponse(
        id=activity.id,
        project_id=activity.project_id,
        actor_id=activity.actor_id,
        actor_name=actor_name,
        task_id=activity.task_id,
        task_title=task.title if task is not None else None,
        activity_type=activity.activity_type,
        details=activity.details,
        created_at=activity.created_at
    )


@router.get(
    "",
    response_model=list[ActivityResponse]
)
def get_project_activities(
    project_id: UUID,
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    activities = activity_service.get_project_activities(
        db,
        project_id,
        current_user,
        limit=limit,
        offset=offset
    )

    return [_serialize_activity(activity) for activity in activities]
