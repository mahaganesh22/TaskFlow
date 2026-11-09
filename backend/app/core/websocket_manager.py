
from uuid import UUID
from fastapi import WebSocket


class ConnectionManager:

    def __init__(self):
        self.project_connections: dict[UUID, set[WebSocket]] = {}
        self.user_connections: dict[UUID, set[WebSocket]] = {}
        self.socket_users: dict[WebSocket, UUID] = {}
        self.socket_projects: dict[WebSocket, UUID] = {}

    async def connect(self, websocket: WebSocket, project_id: UUID, user_id: UUID):
        self.project_connections.setdefault(project_id, set()).add(websocket)
        self.user_connections.setdefault(user_id, set()).add(websocket)

        self.socket_users[websocket] = user_id
        self.socket_projects[websocket] = project_id

    def disconnect(
        self,
        websocket: WebSocket,
        project_id: UUID,
        user_id: UUID
    ):
        self._remove_socket(websocket)

    def _remove_socket(self, websocket: WebSocket):
        user_id = self.socket_users.pop(websocket, None)
        project_id = self.socket_projects.pop(websocket, None)

        if project_id is not None:
            sockets = self.project_connections.get(project_id)

            if sockets:
                sockets.discard(websocket)

                if not sockets:
                    self.project_connections.pop(project_id, None)

        if user_id is not None:
            sockets = self.user_connections.get(user_id)

            if sockets:
                sockets.discard(websocket)

                if not sockets:
                    self.user_connections.pop(user_id, None)

    async def broadcast_to_project(
        self,
        project_id: UUID,
        message: dict
    ):
        connections = self.project_connections.get(project_id, set())

        for websocket in list(connections):
            try:
                await websocket.send_json(message)
            except Exception:
                self._remove_socket(websocket)

    async def send_to_user(
        self,
        user_id: UUID,
        message: dict
    ):
        connections = self.user_connections.get(user_id, set())

        for websocket in list(connections):
            try:
                await websocket.send_json(message)
            except Exception:
                self._remove_socket(websocket)


    async def disconnect_user_from_project(
        self,
        project_id: UUID,
        user_id: UUID
    ):
        user_sockets = list(self.user_connections.get(user_id, set()))

        for websocket in user_sockets:
            if self.socket_projects.get(websocket) != project_id:
                continue

            try:
                await websocket.close(
                    code=4403,
                    reason="Project membership was revoked"
                )
            except Exception:
                pass
            finally:
                self._remove_socket(websocket)


manager = ConnectionManager()
