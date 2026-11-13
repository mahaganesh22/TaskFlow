from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from datetime import datetime, timezone
from uuid import UUID

from app.models import User, Project, ProjectMember
from app.schemas.project_schema import (
    ProjectCreateRequest,
    ProjectUpdateRequest
)
from app.services.authorization_service import (
    verify_project_member,
    verify_project_owner
)


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

        project.updated_at = datetime.now(timezone.utc)

        # 6. Verify membership consistency
        if (
            old_owner_membership is None
            or old_owner_membership.role != "OWNER"
        ):
            raise HTTPException(
                status_code=409,
                detail="Current project ownership is inconsistent"
            )

        if new_owner_membership is None or new_owner_membership.role != "MEMBER":
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


def create_project(
    db: Session,
    project_data: ProjectCreateRequest,
    current_user: User
) -> Project:

    try:
        # 1. Create the project
        project = Project(
            name=project_data.name,
            description=project_data.description,
            tech_stack=project_data.tech_stack,
            owner_id=current_user.id
        )

        db.add(project)

        # 2. Insert the project to obtain its generated ID
        db.flush()

        # 3. Add the creator as the project owner
        membership = ProjectMember(
            project_id=project.id,
            user_id=current_user.id,
            role="OWNER"
        )

        db.add(membership)

        # 4. Commit both records together
        db.commit()
        db.refresh(project)

        return project

    except Exception:
        db.rollback()
        raise


def get_user_projects(
    db: Session,
    current_user: User
) -> list[Project]:

    projects = db.scalars(
        select(Project)
        .join(
            ProjectMember,
            ProjectMember.project_id == Project.id
        )
        .where(
            ProjectMember.user_id == current_user.id
        )
        .order_by(Project.created_at.desc())
    ).all()

    return list(projects)


def get_project_by_id(
    db: Session,
    project_id: UUID,
    current_user: User
) -> Project:

    project = db.get(Project, project_id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    verify_project_member(db, project_id, current_user)

    return project


def update_project(
    db: Session,
    project_id: UUID,
    project_data: ProjectUpdateRequest,
    current_user: User
) -> Project:

    # Lock the project row before checking ownership.
    project = db.scalar(
        select(Project)
        .where(Project.id == project_id)
        .with_for_update()
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    verify_project_owner(db, project_id, current_user)

    update_data = project_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update"
        )

    if "name" in update_data:
        if update_data["name"] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Project name cannot be null"
            )

    try:
        for field, value in update_data.items():
            setattr(project, field, value)

        project.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(project)

        return project

    except Exception:
        db.rollback()
        raise


def delete_project(
    db: Session,
    project_id: UUID,
    current_user: User
) -> None:

    # Lock the project row before checking ownership.
    project = db.scalar(
        select(Project)
        .where(Project.id == project_id)
        .with_for_update()
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    verify_project_owner(db, project_id, current_user)

    try:
        db.delete(project)
        db.commit()

    except Exception:
        db.rollback()
        raise
