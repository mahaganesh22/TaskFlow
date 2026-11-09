from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import User, Task, Comment, ActivityLog
from app.schemas.comment_schema import CommentCreateRequest
from app.services.authorization_service import verify_project_member


def add_comment(
    db: Session,
    project_id: UUID,
    task_id: UUID,
    current_user: User,
    comment_data: CommentCreateRequest
) -> Comment:

    # 1. Verify that the current user is an active project member
    verify_project_member(db, project_id, current_user)

    # 2. Retrieve the task belonging to this project
    task = db.scalar(
        select(Task).where(
            Task.id == task_id,
            Task.project_id == project_id
        )
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    try:
        # 3. Create the comment
        comment = Comment(
            content=comment_data.content,
            task_id=task.id,
            user_id=current_user.id
        )

        db.add(comment)

        # 4. Flush to obtain the generated comment ID
        db.flush()

        # 5. Create activity log
        activity = ActivityLog(
            project_id=project_id,
            actor_id=current_user.id,
            task_id=task.id,
            activity_type="COMMENT_ADDED",
            details={
                "comment_id": str(comment.id)
            }
        )

        db.add(activity)

        # 6. Commit comment and activity together
        db.commit()

        db.refresh(comment)

        return comment

    except Exception:
        db.rollback()
        raise


def get_task_comments(
    db: Session,
    project_id: UUID,
    task_id: UUID,
    current_user: User
) -> list[Comment]:

    # 1. Verify project membership
    verify_project_member(db, project_id, current_user)

    # 2. Verify that the task belongs to this project
    task = db.scalar(
        select(Task).where(
            Task.id == task_id,
            Task.project_id == project_id
        )
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # 3. Retrieve comments in chronological order
    comments = db.scalars(
        select(Comment)
        .where(Comment.task_id == task_id)
        .options(selectinload(Comment.author))
        .order_by(Comment.created_at.asc())
    ).all()

    return comments