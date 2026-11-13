
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
    Task,
    Project,
    ProjectJoinRequest
)

from app.schemas.project_member_schema import ProjectJoinRequestCreate

from app.services.authorization_service import (
    verify_project_owner,
    verify_project_member
)

def invite_member(
    db: Session,
    project_id: UUID,
    current_user: User,
    invite_data: ProjectJoinRequestCreate
) -> ProjectJoinRequest:

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

    # Do not create a join request for someone who already belongs to the project.
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

    join_request = db.scalar(
        select(ProjectJoinRequest)
        .where(
            ProjectJoinRequest.project_id == project_id,
            ProjectJoinRequest.user_id == invited_user.id
        )
        .with_for_update()
    )
    if join_request and join_request.status == "PENDING":
        raise HTTPException(status_code=409, detail="A join request is already pending")
    if join_request and join_request.status == "ACCEPTED":
        raise HTTPException(status_code=409, detail="This user has already accepted the request")

    try:
        if join_request:
            join_request.status = "PENDING"
            join_request.created_at = datetime.now(timezone.utc)
            join_request.responded_at = None
        else:
            join_request = ProjectJoinRequest(
                project_id=project_id,
                user_id=invited_user.id,
                status="PENDING"
            )
            db.add(join_request)
        db.commit()
        db.refresh(join_request)
        return join_request
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="A join request already exists")
    except Exception:
        db.rollback()
        raise


def get_my_join_requests(db: Session, current_user: User) -> list[ProjectJoinRequest]:
    return list(db.scalars(
        select(ProjectJoinRequest)
        .join(ProjectJoinRequest.project)
        .where(
            ProjectJoinRequest.user_id == current_user.id,
            ProjectJoinRequest.status == "PENDING"
        )
        .options(
            selectinload(ProjectJoinRequest.project).selectinload(Project.owner)
        )
        .order_by(ProjectJoinRequest.created_at.desc())
    ).all())


def respond_to_join_request(
    db: Session,
    request_id: UUID,
    current_user: User,
    action: str
) -> ProjectJoinRequest:
    join_request = db.scalar(
        select(ProjectJoinRequest)
        .where(ProjectJoinRequest.id == request_id)
        .options(selectinload(ProjectJoinRequest.project).selectinload(Project.owner))
        .with_for_update()
    )
    if join_request is None:
        raise HTTPException(status_code=404, detail="Join request not found")
    if join_request.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="This join request belongs to another user")
    if join_request.status != "PENDING":
        raise HTTPException(status_code=409, detail="This join request has already been answered")

    try:
        if action == "ACCEPT":
            existing = db.scalar(select(ProjectMember).where(
                ProjectMember.project_id == join_request.project_id,
                ProjectMember.user_id == current_user.id
            ))
            if existing is None:
                db.add(ProjectMember(
                    project_id=join_request.project_id,
                    user_id=current_user.id,
                    role="MEMBER"
                ))
            join_request.status = "ACCEPTED"
        else:
            join_request.status = "REJECTED"
        join_request.responded_at = datetime.now(timezone.utc)

        if action == "ACCEPT":
            db.add(ActivityLog(
                project_id=join_request.project_id,
                actor_id=current_user.id,
                activity_type="MEMBER_JOINED",
                details={"user_id": str(current_user.id)}
            ))
        db.commit()
        db.refresh(join_request)
        return join_request
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


def get_invite_candidates(
    db: Session,
    project_id: UUID,
    current_user: User
) -> list[User]:
    verify_project_owner(db, project_id, current_user)
    existing_member_ids = select(ProjectMember.user_id).where(
        ProjectMember.project_id == project_id
    )
    pending_user_ids = select(ProjectJoinRequest.user_id).where(
        ProjectJoinRequest.project_id == project_id,
        ProjectJoinRequest.status == "PENDING"
    )
    users = db.scalars(
        select(User)
        .where(
            User.deleted_at.is_(None),
            User.id.not_in(existing_member_ids),
            User.id.not_in(pending_user_ids)
        )
        .order_by(User.name.asc(), User.email.asc())
    ).all()
    return list(users)


def remove_project_member(
    db: Session,
    project_id: UUID,
    member_user_id: UUID,
    current_user: User
) -> UUID:

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

        return member_user_id

    except Exception:
        db.rollback()
        raise
