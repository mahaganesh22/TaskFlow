from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.token_service import decode_token
from app.database.database import get_db
from app.models import User


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login"
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )

    try:
        payload = decode_token(token)

        if payload.get("type") != "access":
            raise credentials_exception

        user_id = UUID(payload.get("sub"))

    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise credentials_exception

    user = db.scalar(
        select(User).where(
            User.id == user_id,
            User.deleted_at.is_(None)
        )
    )

    if user is None:
        raise credentials_exception

    return user