from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.models import User
from app.schemas.auth_schema import UserProfileResponse, UserProfileUpdateRequest
from app.services import user_service


router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/me/profile", response_model=UserProfileResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    return user_service.get_user_profile(current_user)


@router.patch("/me/profile", response_model=UserProfileResponse)
def update_my_profile(
    profile_data: UserProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return user_service.update_user_profile(db, current_user, profile_data)


@router.get(
    "/projects/{project_id}/profiles/{profile_user_id}",
    response_model=UserProfileResponse
)
def get_project_profile(
    project_id: UUID,
    profile_user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return user_service.get_project_user_profile(
        db, project_id, profile_user_id, current_user
    )
