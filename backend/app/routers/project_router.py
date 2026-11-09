from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.dependencies import get_current_user
from app.models import User
from app.schemas.project_schema import (
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ProjectResponse,
    TransferOwnershipRequest
)
from app.services import project_service


router = APIRouter(
    prefix="/api/projects",
    tags=["Projects"]
)


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED
)
def create_project(
    project_data: ProjectCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return project_service.create_project(
        db,
        project_data,
        current_user
    )


@router.get(
    "",
    response_model=list[ProjectResponse],
    status_code=status.HTTP_200_OK
)
def get_user_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return project_service.get_user_projects(
        db,
        current_user
    )


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    status_code=status.HTTP_200_OK
)
def get_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return project_service.get_project_by_id(
        db,
        project_id,
        current_user
    )


@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
    status_code=status.HTTP_200_OK
)
def update_project(
    project_id: UUID,
    project_data: ProjectUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return project_service.update_project(
        db,
        project_id,
        project_data,
        current_user
    )


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_200_OK
)
def delete_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project_service.delete_project(
        db,
        project_id,
        current_user
    )

    return {
        "message": "Project deleted successfully"
    }


@router.put(
    "/{project_id}/transfer-ownership",
    response_model=ProjectResponse,
    status_code=status.HTTP_200_OK
)
def transfer_project_ownership(
    project_id: UUID,
    transfer_data: TransferOwnershipRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return project_service.transfer_project_ownership(
        db,
        project_id,
        current_user,
        transfer_data.new_owner_id
    )