
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models import (
    User,
    ProjectMember,
    ActivityLog,
    Task
)

from app.schemas.project_member_schema import ProjectMemberInviteRequest

from app.services.authorization_service import (
    verify_project_owner,
    verify_project_member
)

def invite_member(
    db: Session,
    project_id: UUID,
    current_user: User,
    invite_data: ProjectMemberInviteRequest
) -> ProjectMember:

    # 1. Verify that the current user owns the project
    verify_project_owner(
        db,
        project_id,
        current_user
    )

    # 2. Find the user using their email
    email = str(invite_data.email).strip().lower()

    invited_user = db.scalar(
        select(User).where(
            func.lower(User.email) == email,
            User.deleted_at.is_(None)
        )
    )

    if invited_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active user found with this email"
        )

    # 3. Prevent inviting an existing member
    existing_membership = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == invited_user.id
        )
    )

    if existing_membership is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this project"
        )

    try:
        # 4. Create the membership
        membership = ProjectMember(
            user_id=invited_user.id,
            project_id=project_id,
            role="MEMBER"
        )

        db.add(membership)

        # 5. Flush to make sure the membership insert succeeds
        db.flush()

        # 6. Create activity log
        activity = ActivityLog(
            project_id=project_id,
            actor_id=current_user.id,
            activity_type="MEMBER_INVITED",
            details={
                "invited_user_id": str(invited_user.id)
            }
        )

        db.add(activity)

        # 7. Commit membership and activity together
        db.commit()

        db.refresh(membership)

        return membership

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this project"
        )

    except Exception:
        db.rollback()
        raise


def get_project_members(
    db: Session,
    project_id: UUID,
    current_user: User
) -> list[ProjectMember]:

    # 1. Verify that the current user is an active project member
    verify_project_member(db, project_id, current_user)

    # 2. Retrieve all active members of the project
    members = db.scalars(
        select(ProjectMember)
        .join(ProjectMember.user)
        .where(
            ProjectMember.project_id == project_id,
            User.deleted_at.is_(None)
        )
        .options(
            selectinload(ProjectMember.user)
        )
        .order_by(ProjectMember.joined_at.asc())
    ).all()

    return list(members)


def remove_project_member(
    db: Session,
    project_id: UUID,
    member_user_id: UUID,
    current_user: User
) -> None:

    # 1. Verify that the current user owns the project
    verify_project_owner(
        db,
        project_id,
        current_user
    )

    # 2. Prevent the owner from removing themselves
    if member_user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project owner cannot remove themselves"
        )

    # 3. Retrieve and lock the membership record
    membership = db.scalar(
        select(ProjectMember)
        .where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == member_user_id
        )
        .options(
            selectinload(ProjectMember.user)
        )
        .with_for_update()
    )

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project member not found"
        )

    # 4. Ensure that we are removing a regular member
    if membership.role != "MEMBER":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot remove the project owner"
        )

    try:
        # 5. Unassign all tasks belonging to this member
        db.execute(
            update(Task)
            .where(
                Task.project_id == project_id,
                Task.assignee_id == member_user_id
            )
            .values(
                assignee_id=None,
                updated_at=datetime.now(timezone.utc)
            )
        )

        # 6. Delete the membership record
        db.delete(membership)

        # 7. Create the activity log
        removed_user = membership.user

        activity = ActivityLog(
            project_id=project_id,
            actor_id=current_user.id,
            activity_type="MEMBER_REMOVED",
            details={
                "removed_user_id": str(member_user_id),
                "removed_user_name": (
                    "Deleted User"
                    if removed_user.deleted_at is not None
                    else removed_user.name
                )
            }
        )

        db.add(activity)

        # 8. Commit all changes together
        db.commit()

    except Exception:
        db.rollback()
        raise