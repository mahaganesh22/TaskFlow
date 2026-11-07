from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User, Project, ProjectMember


def transfer_project_ownership(
    db: Session,
    project_id: UUID,
    current_user: User,
    new_owner_id: UUID
) -> Project:

    try:
        # 1. Retrieve and lock the project
        project = db.scalar(
            select(Project)
            .where(Project.id == project_id)
            .with_for_update()
        )

        if project is None:
            raise HTTPException(
                status_code=404,
                detail="Project not found"
            )

        # 2. Verify that the current user owns this project
        if project.owner_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Only the project owner can transfer ownership"
            )

        # 3. Prevent transferring ownership to the same user
        if new_owner_id == current_user.id:
            raise HTTPException(
                status_code=400,
                detail="You are already the project owner"
            )

        # 4. Verify that the new owner has an active account
        new_owner = db.scalar(
            select(User)
            .where(
                User.id == new_owner_id,
                User.deleted_at.is_(None)
            )
        )

        if new_owner is None:
            raise HTTPException(
                status_code=404,
                detail="Active user not found"
            )

        # 5. Retrieve the old and new owner memberships
        memberships = db.scalars(
            select(ProjectMember)
            .where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id.in_([
                    current_user.id,
                    new_owner_id
                ])
            )
            .with_for_update()
        ).all()

        membership_map = {
            membership.user_id: membership
            for membership in memberships
        }

        old_owner_membership = membership_map.get(current_user.id)
        new_owner_membership = membership_map.get(new_owner_id)

        # 6. Verify membership consistency
        if (
            old_owner_membership is None
            or old_owner_membership.role != "OWNER"
        ):
            raise HTTPException(
                status_code=409,
                detail="Current project ownership is inconsistent"
            )

        if new_owner_membership is None:
            raise HTTPException(
                status_code=400,
                detail="New owner must be a project member"
            )

        # 7. Transfer ownership
        project.owner_id = new_owner_id

        old_owner_membership.role = "MEMBER"
        new_owner_membership.role = "OWNER"

        # 8. Commit all changes together
        db.commit()

        db.refresh(project)

        return project

    except Exception:
        db.rollback()
        raise