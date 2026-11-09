
from uuid import UUID

import jwt

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi import HTTPException
from sqlalchemy import select

from app.core.token_service import decode_token
from app.core.websocket_manager import manager
from app.database.database import SessionLocal
from app.models import User
from app.services.authorization_service import verify_project_member


router = APIRouter(tags=["WebSockets"])


@router.websocket("/ws/projects/{project_id}")
async def project_websocket(
    websocket: WebSocket,
    project_id: UUID
):
    await websocket.accept()

    db = SessionLocal()
    current_user = None
    connected = False

    try:
        # 1. Receive the authentication message
        auth_message = await websocket.receive_json()

        if (
            not isinstance(auth_message, dict)
            or auth_message.get("type") != "authenticate"
        ):
            await websocket.close(code=4401)
            return

        token = auth_message.get("token")

        if not isinstance(token, str):
            await websocket.close(code=4401)
            return

        # 2. Validate JWT
        payload = decode_token(token)

        if payload.get("type") != "access":
            await websocket.close(code=4401)
            return

        user_id = UUID(payload["sub"])

        # 3. Retrieve active user
        current_user = db.scalar(
            select(User).where(
                User.id == user_id,
                User.deleted_at.is_(None)
            )
        )

        if current_user is None:
            await websocket.close(code=4401)
            return

        # 4. Verify project membership
        try:
            verify_project_member(
                db,
                project_id,
                current_user
            )
        except HTTPException:
            await websocket.close(code=4403)
            return

        # 5. Register authenticated connection
        await manager.connect(
            websocket,
            project_id,
            current_user.id
        )

        connected = True

        await websocket.send_json({
            "type": "CONNECTED",
            "project_id": str(project_id)
        })

        # 6. Keep connection alive
        while True:
            message = await websocket.receive_json()

            if isinstance(message, dict) and message.get("type") == "ping":
                await websocket.send_json({
                    "type": "pong"
                })
            else:
                await websocket.send_json({
                    "type": "ERROR",
                    "message": "Unsupported WebSocket message"
                })

    except WebSocketDisconnect:
        pass

    except (
        jwt.InvalidTokenError,
        ValueError,
        TypeError,
        KeyError
    ):
        try:
            await websocket.close(code=4401)
        except Exception:
            pass

    finally:
        if connected and current_user is not None:
            manager.disconnect(
                websocket,
                project_id,
                current_user.id
            )

        db.close()
