from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.auth_schema import (
    RegisterRequest,
    LoginRequest,
    AuthResponse,
    RefreshTokenRequest,
    LogoutRequest
)
from app.services.auth_service import (
    register_user,
    login_user,
    refresh_tokens,
    logout_user
)


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED
)
def register(
    user_data: RegisterRequest,
    db: Session = Depends(get_db)
):
    return register_user(db, user_data)


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK
)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    return login_user(db, login_data)


@router.post(
    "/refresh",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK
)
def refresh(
    token_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    return refresh_tokens(db, token_data.refresh_token)


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK
)
def logout(
    token_data: LogoutRequest,
    db: Session = Depends(get_db)
):
    logout_user(db, token_data.refresh_token)

    return {
        "message": "Successfully logged out"
    }