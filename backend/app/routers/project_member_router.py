from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.dependencies import get_current_user
from app.models import User

from app.schemas.project_member_schema import (
    ProjectJoinRequestCreate,
    ProjectJoinRequestResponse,
    ProjectJoinRequestAction,
    ProjectMemberResponse
)
from app.schemas.auth_schema import UserPublicResponse

from app.services import project_member_service

from fastapi import BackgroundTasks
from app.core.websocket_manager import manager


router = APIRouter(
    prefix="/api/projects/{project_id}/members",
    tags=["Project Members"]
)

requests_router = APIRouter(prefix="/api/join-requests", tags=["Project Join Requests"])


@router.get("/invite-candidates", response_model=list[UserPublicResponse])
def get_invite_candidates(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return project_member_service.get_invite_candidates(db, project_id, current_user)


@router.post(
    "",
    response_model=ProjectJoinRequestResponse,
    status_code=status.HTTP_201_CREATED
)
def invite_member(
    project_id: UUID,
    invite_data: ProjectJoinRequestCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    membership = project_member_service.invite_member(
        db,
        project_id,
        current_user,
        invite_data
    )

    event = {
        "type": "PROJECT_JOIN_REQUESTED",
        "project_id": str(project_id),
        "request_id": str(membership.id),
        "user_id": str(membership.user_id)
    }

    background_tasks.add_task(
        manager.send_to_user,
        membership.user_id,
        event
    )

    return membership


@requests_router.get("/me", response_model=list[ProjectJoinRequestResponse])
def get_my_join_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return project_member_service.get_my_join_requests(db, current_user)


@requests_router.post("/{request_id}/respond", response_model=ProjectJoinRequestResponse)
def respond_to_join_request(
    request_id: UUID,
    action_data: ProjectJoinRequestAction,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    join_request = project_member_service.respond_to_join_request(
        db, request_id, current_user, action_data.action
    )
    event = {
        "type": "PROJECT_JOIN_REQUEST_RESPONDED",
        "project_id": str(join_request.project_id),
        "request_id": str(join_request.id),
        "user_id": str(current_user.id),
        "status": join_request.status
    }
    background_tasks.add_task(manager.send_to_user, join_request.project.owner_id, event)
    background_tasks.add_task(manager.send_to_user, current_user.id, event)
    if join_request.status == "ACCEPTED":
        background_tasks.add_task(manager.broadcast_to_project, join_request.project_id, {
            "type": "MEMBER_JOINED",
            "project_id": str(join_request.project_id),
            "user_id": str(current_user.id)
        })
    return join_request


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
async def remove_project_member(
    project_id: UUID,
    member_user_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    removed_user_id = project_member_service.remove_project_member(
        db,
        project_id,
        member_user_id,
        current_user
    )

    # Close the removed member's connection to this project.
    await manager.disconnect_user_from_project(
        project_id,
        removed_user_id
    )

    event = {
        "type": "MEMBER_REMOVED",
        "project_id": str(project_id),
        "user_id": str(removed_user_id)
    }

    # Notify the remaining project members.
    background_tasks.add_task(
        manager.broadcast_to_project,
        project_id,
        event
    )

    # Personal socket stays open so Assigned to Me can refresh.
    background_tasks.add_task(
        manager.send_to_user,
        removed_user_id,
        event
    )

    return {
        "message": "Project member removed successfully"
    }
