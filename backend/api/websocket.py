from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ws.manager import manager

router = APIRouter()


@router.websocket("/ws/progress/{session_id}")
async def websocket_progress(ws: WebSocket, session_id: str):
    await manager.connect(session_id, ws)
    try:
        while True:
            await ws.receive_text()  # keep-alive / client pings
    except WebSocketDisconnect:
        await manager.disconnect(session_id)
