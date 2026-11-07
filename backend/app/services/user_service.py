from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models import User, Project, Task


def soft_delete_user(db: Session, user: User) -> User:

    # 1. Check whether the account is already deleted
    if user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account has already been deleted"
        )

    # 2. Check whether the user owns any projects
    owned_project = db.scalar(
        select(Project.id)
        .where(Project.owner_id == user.id)
        .limit(1)
    )

    if owned_project is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Transfer ownership or delete your projects before deleting your account"
        )

    try:
        # 3. Unassign tasks assigned to this user
        db.execute(
            update(Task)
            .where(Task.assignee_id == user.id)
            .values(assignee_id=None)
        )

        # 4. Soft-delete the user
        user.deleted_at = datetime.now(timezone.utc)

        # 5. Save changes
        db.commit()

        db.refresh(user)

        return user

    except Exception:
        db.rollback()
        raise