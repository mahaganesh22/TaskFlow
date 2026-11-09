from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.dependencies import get_current_user
from app.models import User

from app.schemas.project_member_schema import (
    ProjectMemberInviteRequest,
    ProjectMemberResponse
)

from app.services import project_member_service


router = APIRouter(
    prefix="/api/projects/{project_id}/members",
    tags=["Project Members"]
)


@router.post(
    "",
    response_model=ProjectMemberResponse,
    status_code=status.HTTP_201_CREATED
)
def invite_member(
    project_id: UUID,
    invite_data: ProjectMemberInviteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return project_member_service.invite_member(
        db,
        project_id,
        current_user,
        invite_data
    )


@router.get(
    "",
    response_model=list[ProjectMemberResponse],
    status_code=status.HTTP_200_OK
)
def get_project_members(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return project_member_service.get_project_members(
        db,
        project_id,
        current_user
    )


@router.delete(
    "/{member_user_id}",
    status_code=status.HTTP_200_OK
)
def remove_project_member(
    project_id: UUID,
    member_user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project_member_service.remove_project_member(
        db,
        project_id,
        member_user_id,
        current_user
    )

    return {
        "message": "Project member removed successfully"
    }