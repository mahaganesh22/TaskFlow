
import asyncio
import json
from uuid import UUID

import jwt

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.token_service import decode_token
from app.core.websocket_manager import manager
from app.database.database import SessionLocal
from app.models import User
from app.services.authorization_service import verify_project_member


router = APIRouter(tags=["WebSockets"])

AUTH_TIMEOUT_SECONDS = 10.0


async def _close_websocket(
    websocket: WebSocket,
    code: int,
    reason: str = ""
) -> None:
    try:
        await websocket.close(code=code, reason=reason)
    except Exception:
        pass


async def authenticate_websocket(
    websocket: WebSocket,
    db: Session
) -> User | None:
    try:
        auth_message = await asyncio.wait_for(
            websocket.receive_json(),
            timeout=AUTH_TIMEOUT_SECONDS
        )
    except asyncio.TimeoutError:
        await _close_websocket(
            websocket,
            4401,
            "Authentication timed out"
        )
        return None
    except WebSocketDisconnect:
        return None
    except (json.JSONDecodeError, ValueError, TypeError, KeyError):
        await _close_websocket(
            websocket,
            4401,
            "Malformed authentication message"
        )
        return None

    if (
        not isinstance(auth_message, dict)
        or auth_message.get("type") != "authenticate"
    ):
        await _close_websocket(
            websocket,
            4401,
            "Invalid authentication message"
        )
        return None

    token = auth_message.get("token")

    if not isinstance(token, str) or not token.strip():
        await _close_websocket(
            websocket,
            4401,
            "Missing access token"
        )
        return None

    try:
        payload = decode_token(token)
    except jwt.InvalidTokenError:
        await _close_websocket(
            websocket,
            4401,
            "Invalid or expired token"
        )
        return None

    if payload.get("type") != "access":
        await _close_websocket(
            websocket,
            4401,
            "Invalid token type"
        )
        return None

    try:
        user_id = UUID(payload["sub"])
    except (KeyError, ValueError, TypeError):
        await _close_websocket(
            websocket,
            4401,
            "Invalid token"
        )
        return None

    current_user = db.scalar(
        select(User).where(
            User.id == user_id,
            User.deleted_at.is_(None)
        )
    )

    if current_user is None:
        await _close_websocket(
            websocket,
            4401,
            "Invalid or expired token"
        )
        return None

    return current_user


async def _keep_connection_alive(websocket: WebSocket) -> None:
    while True:
        try:
            message = await websocket.receive_json()
        except json.JSONDecodeError:
            await websocket.send_json({
                "type": "ERROR",
                "message": "Malformed WebSocket message"
            })
            continue

        if isinstance(message, dict) and message.get("type") == "ping":
            await websocket.send_json({
                "type": "pong"
            })
        else:
            await websocket.send_json({
                "type": "ERROR",
                "message": "Unsupported WebSocket message"
            })


@router.websocket("/ws/users/me")
async def user_websocket(websocket: WebSocket):
    await websocket.accept()

    db = SessionLocal()
    connected = False

    try:
        current_user = await authenticate_websocket(websocket, db)

        if current_user is None:
            return

        await manager.connect_user(websocket, current_user.id)
        connected = True

        await websocket.send_json({
            "type": "CONNECTED",
            "scope": "user"
        })

        await _keep_connection_alive(websocket)

    except WebSocketDisconnect:
        pass

    except (
        jwt.InvalidTokenError,
        ValueError,
        TypeError,
        KeyError
    ):
        await _close_websocket(websocket, 4401, "Invalid or expired token")

    finally:
        if connected:
            manager.disconnect(websocket)

        db.close()


@router.websocket("/ws/projects/{project_id}")
async def project_websocket(
    websocket: WebSocket,
    project_id: UUID
):
    await websocket.accept()

    db = SessionLocal()
    connected = False

    try:
        current_user = await authenticate_websocket(websocket, db)

        if current_user is None:
            return

        try:
            verify_project_member(
                db,
                project_id,
                current_user
            )
        except HTTPException:
            await _close_websocket(
                websocket,
                4403,
                "Not a member of this project"
            )
            return

        await manager.connect_project(
            websocket,
            project_id,
            current_user.id
        )
        connected = True

        await websocket.send_json({
            "type": "CONNECTED",
            "scope": "project",
            "project_id": str(project_id)
        })

        await _keep_connection_alive(websocket)

    except WebSocketDisconnect:
        pass

    except (
        jwt.InvalidTokenError,
        ValueError,
        TypeError,
        KeyError
    ):
        await _close_websocket(websocket, 4401, "Invalid or expired token")

    finally:
        if connected:
            manager.disconnect(websocket)

        db.close()
