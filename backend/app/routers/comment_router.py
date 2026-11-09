
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    status,
    BackgroundTasks
)

from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.dependencies import get_current_user
from app.core.websocket_manager import manager

from app.models import User
from app.schemas.comment_schema import (
    CommentCreateRequest,
    CommentResponse
)

from app.services import comment_service


router = APIRouter(
    prefix="/api/projects/{project_id}/tasks/{task_id}/comments",
    tags=["Comments"]
)


@router.post(
    "",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED
)
def add_comment(
    project_id: UUID,
    task_id: UUID,
    comment_data: CommentCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    comment = comment_service.add_comment(
        db,
        project_id,
        task_id,
        current_user,
        comment_data
    )

    background_tasks.add_task(
        manager.broadcast_to_project,
        project_id,
        {
            "type": "COMMENT_ADDED",
            "project_id": str(project_id),
            "task_id": str(task_id),
            "comment_id": str(comment.id)
        }
    )

    return {
        "id": comment.id,
        "content": comment.content,
        "task_id": comment.task_id,
        "user_id": comment.user_id,
        "author_name": current_user.name,
        "created_at": comment.created_at
    }


@router.get(
    "",
    response_model=list[CommentResponse]
)
def get_task_comments(
    project_id: UUID,
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    comments = comment_service.get_task_comments(
        db,
        project_id,
        task_id,
        current_user
    )

    return [
        {
            "id": comment.id,
            "content": comment.content,
            "task_id": comment.task_id,
            "user_id": comment.user_id,
            "author_name": (
                comment.author.name
                if comment.author and comment.author.deleted_at is None
                else "Deleted User"
            ),
            "created_at": comment.created_at
        }
        for comment in comments
    ]
