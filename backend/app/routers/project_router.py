from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models import User
from app.schemas.project_schema import TransferOwnershipRequest
from app.services.project_service import transfer_project_ownership

from app.core.security import get_current_user


router = APIRouter(
    prefix="/api/projects",
    tags=["Projects"]
)


@router.put("/{project_id}/transfer-ownership")
def transfer_ownership(
    project_id: UUID,
    request: TransferOwnershipRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    project = transfer_project_ownership(
        db=db,
        project_id=project_id,
        current_user=current_user,
        new_owner_id=request.new_owner_id
    )

    return {
        "message": "Project ownership transferred successfully",
        "project_id": str(project.id),
        "new_owner_id": str(project.owner_id)
    }