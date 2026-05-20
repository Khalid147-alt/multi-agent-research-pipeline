import asyncio
import io
import logging
import re
import uuid

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

from api.report_parser import (
    chart_data,
    extract_sources,
    parse_sections,
    render_pdf_html,
)
from crew.research_crew import run_research
from db.adapter import USE_SQLITE, get_pool

logger = logging.getLogger(__name__)
router = APIRouter()


# Reject control characters and obvious script-injection payloads at the
# pydantic boundary. We don't strip — we 422 the request so abuse attempts
# don't get stored.
_TOPIC_REJECT_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f<>{}]")


class ResearchRequest(BaseModel):
    topic: str = Field(min_length=5, max_length=300)

    @field_validator("topic")
    @classmethod
    def _clean(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Topic cannot be empty.")
        if _TOPIC_REJECT_RE.search(v):
            raise ValueError("Topic contains disallowed characters.")
        return v


async def _safe_run_research(session_id: str, topic: str):
    """Outer safety net — guarantees the session row never stays stuck on
    'running' if the worker dies (cancellation, OOM, unhandled exception)."""
    try:
        await run_research(session_id, topic)
    except BaseException as e:  # noqa: BLE001
        logger.exception("Background research task failed for %s: %s", session_id, e)
        try:
            pool = get_pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    "UPDATE sessions SET status='failed' "
                    "WHERE id=$1 AND status='running'",
                    session_id,
                )
        except Exception:
            logger.exception("Could not mark session %s as failed", session_id)


@router.post("/research")
async def start_research(req: ResearchRequest, request: Request):
    session_id = str(uuid.uuid4())
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO sessions (id, topic, status) VALUES ($1, $2, 'running')",
            session_id,
            req.topic,
        )
    asyncio.create_task(_safe_run_research(session_id, req.topic))
    # Stash on app state so the WebSocket handler can verify the binding.
    request.app.state.recent_sessions = getattr(
        request.app.state, "recent_sessions", {}
    )
    request.app.state.recent_sessions[session_id] = asyncio.get_running_loop().time()
    return {"session_id": session_id, "status": "started"}


@router.get("/report/{session_id}")
async def get_report(session_id: str, request: Request):
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM reports WHERE session_id=$1", session_id
        )
        if not row:
            sess = await conn.fetchrow(
                "SELECT topic, status FROM sessions WHERE id=$1", session_id
            )
        else:
            sess = None

    if not row:
        if not sess:
            return {"status": "not_found"}
        return {
            "status": sess["status"],  # running | failed | complete (no row yet)
            "topic": sess["topic"],
        }

    content = row["content"] or ""
    parsed = parse_sections(content)
    return {
        "status": "complete",
        "topic": row["topic"],
        "content": content,
        "parsed_sections": [s.to_dict() for s in parsed],
        "chart_data": chart_data(parsed),
        "sources": extract_sources(content),
        "pdf_path": row.get("pdf_path") if isinstance(row, dict) else row["pdf_path"],
    }


@router.get("/report/{session_id}/pdf")
async def get_report_pdf(session_id: str, request: Request):
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT topic, content FROM reports WHERE session_id=$1", session_id
        )
    if not row or not row.get("content"):
        raise HTTPException(status_code=404, detail="Report not ready")

    try:
        from weasyprint import HTML  # lazy: needs GTK; works on HF Linux
    except (ImportError, OSError) as e:
        raise HTTPException(
            status_code=503,
            detail=f"PDF rendering unavailable on this host: {e}",
        )

    html_doc = render_pdf_html(row["topic"], row["content"])
    pdf_bytes = HTML(string=html_doc).write_pdf()
    safe_name = re.sub(r"[^a-zA-Z0-9_-]+", "-", row["topic"])[:60].strip("-") or "report"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_name}-{session_id[:8]}.pdf"'
        },
    )


# Stuck-session reaper: if a session has been 'running' for >15 min, the
# worker is gone (HF cold-start kill, OOM, uncaught error). Mark it failed
# so /history doesn't show stale rows. Runs lazily on every /history fetch.
_STUCK_SQL_SQLITE = (
    "UPDATE sessions SET status='failed' "
    "WHERE status='running' "
    "AND datetime(created_at) < datetime('now', '-15 minutes')"
)
_STUCK_SQL_PG = (
    "UPDATE sessions SET status='failed' "
    "WHERE status='running' "
    "AND created_at < NOW() - INTERVAL '15 minutes'"
)


@router.get("/history")
async def get_history(request: Request):
    pool = get_pool()
    async with pool.acquire() as conn:
        try:
            await conn.execute(_STUCK_SQL_SQLITE if USE_SQLITE else _STUCK_SQL_PG)
        except Exception:
            logger.exception("Stuck-session reaper failed (non-fatal)")

        rows = await conn.fetch(
            "SELECT id, topic, status, created_at FROM sessions "
            "ORDER BY created_at DESC LIMIT 20"
        )
    return [dict(r) for r in rows]
