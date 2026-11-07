from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import ActivityLog, User
from app.services.authorization_service import verify_project_member


def get_project_activities(
    db: Session,
    project_id: UUID,
    current_user: User,
    limit: int = 20,
    offset: int = 0
) -> list[ActivityLog]:

    # 1. Verify that the user is an active project member
    verify_project_member(db, project_id, current_user)

    # 2. Retrieve activities belonging to this project
    activities = db.scalars(
        select(ActivityLog)
        .where(ActivityLog.project_id == project_id)
        .options(
            selectinload(ActivityLog.actor),
            selectinload(ActivityLog.task)
        )
        .order_by(
            ActivityLog.created_at.desc(),
            ActivityLog.id.desc()
        )
        .limit(limit)
        .offset(offset)
    ).all()

    return list(activities)