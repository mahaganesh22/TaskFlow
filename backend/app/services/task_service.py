from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    User,
    ProjectMember,
    Task,
    ActivityLog
)

from app.schemas.task_schema import TaskCreateRequest, TaskUpdateRequest, TaskAssignmentRequest, TaskStatusUpdateRequest

from app.services.authorization_service import verify_project_owner, verify_task_assignee_or_owner


def create_task(
    db: Session,
    project_id: UUID,
    current_user: User,
    task_data: TaskCreateRequest
) -> Task:

    # 1. Verify that the current user owns the project
    verify_project_owner(
        db,
        project_id,
        current_user
    )

    # 2. Validate the due date
    if task_data.due_date is not None:

        if task_data.due_date <= datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Due date cannot be in the past"
            )

    # 3. Validate the assignee, if provided
    if task_data.assignee_id is not None:

        membership = db.scalar(
            select(ProjectMember)
            .where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == task_data.assignee_id,
                ProjectMember.user.has(
                    User.deleted_at.is_(None)
                )
            )
            .with_for_update()
        )

        if membership is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignee must be an active member of this project"
            )

    try:

        # 4. Create the task
        task = Task(
            title=task_data.title,
            description=task_data.description,
            status="TODO",
            priority=task_data.priority,
            due_date=task_data.due_date,
            project_id=project_id,
            created_by=current_user.id,
            assignee_id=task_data.assignee_id
        )

        db.add(task)

        # 5. Send INSERT to database to obtain generated task ID
        db.flush()

        # 6. Record task creation activity
        created_activity = ActivityLog(
            project_id=project_id,
            actor_id=current_user.id,
            task_id=task.id,
            activity_type="TASK_CREATED",
            details={
                "title": task.title
            }
        )

        db.add(created_activity)

        # 7. Record assignment activity, if assigned
        if task.assignee_id is not None:

            assigned_activity = ActivityLog(
                project_id=project_id,
                actor_id=current_user.id,
                task_id=task.id,
                activity_type="TASK_ASSIGNED",
                details={
                    "assignee_id": str(task.assignee_id)
                }
            )

            db.add(assigned_activity)

        # 8. Commit task and activity records together
        db.commit()

        db.refresh(task)

        return task

    except Exception:
        db.rollback()
        raise


def update_task_details(
    db: Session,
    project_id: UUID,
    task_id: UUID,
    current_user: User,
    task_data: TaskUpdateRequest
) -> Task:

    # 1. Verify project ownership
    verify_project_owner(
        db,
        project_id,
        current_user
    )

    # 2. Retrieve the task belonging to this project
    task = db.scalar(
        select(Task)
        .where(
            Task.id == task_id,
            Task.project_id == project_id
        )
        .with_for_update()
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # 3. Identify fields explicitly provided by the client
    updates = task_data.model_dump(exclude_unset=True)

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update"
        )

    # 4. Prevent null values for mandatory fields
    if "title" in updates and updates["title"] is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Task title cannot be null"
        )

    if "priority" in updates and updates["priority"] is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Task priority cannot be null"
        )

    # 5. Apply the requested changes
    try:

        for field, value in updates.items():
            setattr(task, field, value)

        db.commit()

        db.refresh(task)

        return task

    except Exception:
        db.rollback()
        raise



def assign_task(
    db: Session,
    project_id: UUID,
    task_id: UUID,
    current_user: User,
    assignment_data: TaskAssignmentRequest
) -> Task:

    # 1. Verify project ownership
    verify_project_owner(
        db,
        project_id,
        current_user
    )

    # 2. Verify the assignee is an active project member
    new_assignee = db.scalar(
        select(ProjectMember)
        .where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == assignment_data.assignee_id,
            ProjectMember.user.has(
                User.deleted_at.is_(None)
            )
        )
        .with_for_update()
    )

    if new_assignee is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assignee must be an active member of this project"
        )

    # 3. Retrieve and lock the task
    task = db.scalar(
        select(Task)
        .where(
            Task.id == task_id,
            Task.project_id == project_id
        )
        .with_for_update()
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # 4. Check whether the task is already assigned to this user
    if task.assignee_id == assignment_data.assignee_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task is already assigned to this user"
        )

    try:

        # 5. Store the previous assignee
        old_assignee_id = task.assignee_id

        # 6. Update the task assignment
        task.assignee_id = assignment_data.assignee_id

        # 7. Create activity log
        activity = ActivityLog(
            project_id=project_id,
            actor_id=current_user.id,
            task_id=task.id,
            activity_type="TASK_ASSIGNED",
            details={
                "old_assignee_id": (
                    str(old_assignee_id)
                    if old_assignee_id else None
                ),
                "new_assignee_id": str(task.assignee_id)
            }
        )

        db.add(activity)

        # 8. Commit changes together
        db.commit()

        db.refresh(task)

        return task

    except Exception:
        db.rollback()
        raise


def update_task_status(
    db: Session,
    project_id: UUID,
    task_id: UUID,
    current_user: User,
    status_data: TaskStatusUpdateRequest
) -> Task:

    # 1. Retrieve the task and lock it for this transaction
    task = db.scalar(
        select(Task)
        .where(
            Task.id == task_id,
            Task.project_id == project_id
        )
        .with_for_update()
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # 2. Verify whether the user can update this task
    verify_task_assignee_or_owner(db, task, current_user)

    new_status = status_data.status

    # 3. Avoid creating duplicate activity for an unchanged status
    if task.status == new_status:
        return task

    old_status = task.status

    try:
        # 4. Update the task status
        task.status = new_status

        # 5. Maintain completed_at according to the new status
        if new_status == "DONE":
            task.completed_at = datetime.now(timezone.utc)
        else:
            task.completed_at = None

        # 6. Record the status change in the activity log
        activity = ActivityLog(
            project_id=project_id,
            actor_id=current_user.id,
            task_id=task.id,
            activity_type="TASK_STATUS_CHANGED",
            details={
                "old_status": old_status,
                "new_status": new_status
            }
        )

        db.add(activity)

        # 7. Save both changes in one transaction
        db.commit()
        db.refresh(task)

        return task

    except Exception:
        db.rollback()
        raise


def delete_task(
    db: Session,
    project_id: UUID,
    task_id: UUID,
    current_user: User
) -> None:

    # 1. Verify that the current user owns the project
    verify_project_owner(
        db,
        project_id,
        current_user
    )

    # 2. Retrieve and lock the task
    task = db.scalar(
        select(Task)
        .where(
            Task.id == task_id,
            Task.project_id == project_id
        )
        .with_for_update()
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    try:
        # 3. Delete the task
        db.delete(task)

        # 4. Commit the deletion
        db.commit()

    except Exception:
        db.rollback()
        raise