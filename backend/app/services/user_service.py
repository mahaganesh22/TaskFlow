from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models import User, Project, Task
from app.services.authorization_service import verify_project_owner
from app.schemas.auth_schema import UserProfileUpdateRequest
from uuid import UUID


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


def get_user_profile(user: User) -> User:
    return user


def update_user_profile(
    db: Session,
    user: User,
    profile_data: UserProfileUpdateRequest
) -> User:
    changes = profile_data.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide at least one profile field to update"
        )
    try:
        for field, value in changes.items():
            setattr(user, field, value)
        db.commit()
        db.refresh(user)
        return user
    except Exception:
        db.rollback()
        raise


def get_project_user_profile(
    db: Session,
    project_id: UUID,
    profile_user_id: UUID,
    current_user: User
) -> User:
    verify_project_owner(db, project_id, current_user)
    profile_user = db.scalar(select(User).where(
        User.id == profile_user_id,
        User.deleted_at.is_(None)
    ))
    if profile_user is None:
        raise HTTPException(status_code=404, detail="User profile not found")

    # The owner-only authorization allows inspection of both team members and
    # eligible invite candidates, whose profiles are intentionally discoverable.
    return profile_user
