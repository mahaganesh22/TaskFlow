from datetime import datetime, timezone
from uuid import UUID

import jwt
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import User, RefreshToken
from app.schemas.auth_schema import RegisterRequest, LoginRequest, AuthResponse
from app.core.security import hash_password, verify_password
from app.core.token_service import (
    create_access_token,
    create_refresh_token,
    decode_token
)


def _generate_tokens(db: Session, user: User) -> tuple[str, str]:
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    payload = decode_token(refresh_token)

    refresh_record = RefreshToken(
        jti=payload["jti"],
        user_id=user.id,
        expires_at=datetime.fromtimestamp(
            payload["exp"],
            tz=timezone.utc
        )
    )

    db.add(refresh_record)

    return access_token, refresh_token


def register_user(
    db: Session,
    user_data: RegisterRequest
) -> AuthResponse:

    existing_user = db.scalar(
        select(User).where(
            func.lower(User.email) == user_data.email.lower()
        )
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered"
        )

    user = User(
        name=user_data.name,
        email=user_data.email.lower(),
        password_hash=hash_password(user_data.password)
    )

    try:
        db.add(user)
        db.flush()

        access_token, refresh_token = _generate_tokens(db, user)

        db.commit()
        db.refresh(user)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered"
        )

    except Exception:
        db.rollback()
        raise

    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user
    )


def login_user(
    db: Session,
    login_data: LoginRequest
) -> AuthResponse:

    user = db.scalar(
        select(User).where(
            func.lower(User.email) == login_data.email.lower(),
            User.deleted_at.is_(None)
        )
    )

    if user is None or not verify_password(
        login_data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        access_token, refresh_token = _generate_tokens(db, user)

        db.commit()
        db.refresh(user)

    except Exception:
        db.rollback()
        raise

    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user
    )


def refresh_tokens(
    db: Session,
    refresh_token: str
) -> AuthResponse:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token"
    )

    try:
        payload = decode_token(refresh_token)

        if payload.get("type") != "refresh":
            raise credentials_exception

        user_id = UUID(payload["sub"])
        jti = payload["jti"]

        if not isinstance(jti, str) or not jti:
            raise credentials_exception

        expires_at = datetime.fromtimestamp(
            payload["exp"],
            tz=timezone.utc
        )

    except (jwt.InvalidTokenError, ValueError, TypeError, KeyError):
        raise credentials_exception

    now = datetime.now(timezone.utc)

    try:
        stored_token = db.scalar(
            select(RefreshToken)
            .where(
                RefreshToken.jti == jti,
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > now
            )
            .with_for_update()
        )

        if stored_token is None:
            raise credentials_exception

        user = db.scalar(
            select(User).where(
                User.id == user_id,
                User.deleted_at.is_(None)
            )
        )

        if user is None:
            raise credentials_exception

        stored_token.revoked_at = now

        access_token, new_refresh_token = _generate_tokens(db, user)

        db.commit()
        db.refresh(user)

    except Exception:
        db.rollback()
        raise

    return AuthResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        user=user
    )


def logout_user(
    db: Session,
    refresh_token: str
) -> None:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token"
    )

    try:
        payload = decode_token(refresh_token)

        if payload.get("type") != "refresh":
            raise credentials_exception

        user_id = UUID(payload["sub"])
        jti = payload["jti"]

        if not isinstance(jti, str) or not jti:
            raise credentials_exception

    except (jwt.InvalidTokenError, ValueError, TypeError, KeyError):
        raise credentials_exception

    try:
        stored_token = db.scalar(
            select(RefreshToken)
            .where(
                RefreshToken.jti == jti,
                RefreshToken.user_id == user_id
            )
            .with_for_update()
        )

        # Logout is idempotent: an already-revoked token
        # does not need to be revoked again.
        if stored_token is not None and stored_token.revoked_at is None:
            stored_token.revoked_at = datetime.now(timezone.utc)

        db.commit()

    except Exception:
        db.rollback()
        raise