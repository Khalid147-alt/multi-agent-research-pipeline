from typing import Dict

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active: Dict[str, WebSocket] = {}
        self.sessions: Dict[str, dict] = {}  # replaces Redis on HF

    async def connect(self, session_id: str, ws: WebSocket):
        await ws.accept()
        self.active[session_id] = ws

    async def disconnect(self, session_id: str):
        self.active.pop(session_id, None)

    async def broadcast(self, session_id: str, event: dict):
        ws = self.active.get(session_id)
        if ws:
            try:
                await ws.send_json(event)
            except Exception:
                await self.disconnect(session_id)


manager = ConnectionManager()
