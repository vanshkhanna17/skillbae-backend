from fastapi import WebSocket


class ConnectionManager:

    def __init__(self) -> None:
        self.active: dict[int, list[WebSocket]] = {}

    def connect(self, user_id: int, ws: WebSocket):
        if user_id not in self.active:
            self.active[user_id] = []
        self.active[user_id].append(ws)

    def disconnect(self, user_id: int, ws: WebSocket) -> bool:
        if user_id not in self.active:
            return True

        self.active[user_id].remove(ws)

        if not self.active[user_id]:
            del self.active[user_id]
            return True

        return False

    async def send_to_user(self, user_id: int, message: dict):
        connections: list[WebSocket] = self.active.get(user_id, [])
        dead: list[WebSocket] = []
        for ws in connections:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)

        for ws in dead:
            self.disconnect(user_id, ws)

    async def broadcast(self, message: dict):
        dead: list[tuple[int, WebSocket]] = []
        for user_id, connections in self.active.items():
            for ws in connections:
                try:
                    await ws.send_json(message)
                except Exception:
                    dead.append((user_id, ws))

        for user_id, ws in dead:
            self.disconnect(user_id, ws)


ws_connection_manger: ConnectionManager = ConnectionManager()
