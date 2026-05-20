"""
WebSocket endpoint for live agent progress events.

Session-id binding: a client may only subscribe to a session_id that exists
in the `sessions` table AND was created within the last hour. This prevents
random clients from snooping on other users' research streams by guessing
session ids.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from db.adapter import USE_SQLITE, get_pool
from ws.manager import manager

router = APIRouter()


_SESSION_LOOKUP_SQLITE = (
    "SELECT id FROM sessions "
    "WHERE id=$1 AND datetime(created_at) > datetime('now', '-60 minutes')"
)
_SESSION_LOOKUP_PG = (
    "SELECT id FROM sessions "
    "WHERE id=$1 AND created_at > NOW() - INTERVAL '60 minutes'"
)


async def _is_known_session(session_id: str) -> bool:
    try:
        pool = get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                _SESSION_LOOKUP_SQLITE if USE_SQLITE else _SESSION_LOOKUP_PG,
                session_id,
            )
        return row is not None
    except Exception:
        # If the DB lookup itself errors, fail closed (refuse the connection).
        return False


@router.websocket("/ws/progress/{session_id}")
async def websocket_progress(ws: WebSocket, session_id: str):
    if not session_id or len(session_id) > 64:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    if not await _is_known_session(session_id):
        # Accept then immediately close with a custom 4404, so the browser
        # surfaces a clean reason instead of a generic handshake failure.
        await ws.accept()
        await ws.close(code=4404, reason="Unknown or expired session")
        return

    await manager.connect(session_id, ws)
    try:
        while True:
            await ws.receive_text()  # ping/keep-alive
    except WebSocketDisconnect:
        await manager.disconnect(session_id)
