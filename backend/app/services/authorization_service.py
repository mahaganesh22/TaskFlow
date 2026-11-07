
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User, Project, ProjectMember, Task


def verify_project_member(
    db: Session,
    project_id: UUID,
    user: User
) -> ProjectMember:

    membership = db.scalar(
        select(ProjectMember)
        .where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user.id,
            ProjectMember.user.has(
                User.deleted_at.is_(None)
            )
        )
    )

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not an active member of this project"
        )

    return membership


def verify_project_owner(
    db: Session,
    project_id: UUID,
    user: User
) -> Project:

    project = db.scalar(
        select(Project)
        .where(Project.id == project_id)
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    if project.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the project owner can perform this action"
        )

    membership = verify_project_member(
        db,
        project_id,
        user
    )

    if membership.role != "OWNER":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Project ownership and membership role are inconsistent"
        )

    return project


def verify_task_assignee_or_owner(
    db: Session,
    task: Task,
    user: User
) -> None:

    membership = verify_project_member(
        db,
        task.project_id,
        user
    )

    if membership.role == "OWNER":
        return

    if task.assignee_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update tasks assigned to you"
        )
