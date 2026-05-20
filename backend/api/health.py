from fastapi import APIRouter

from db.adapter import USE_SQLITE, get_pool

router = APIRouter()


@router.get("/health")
async def health():
    if USE_SQLITE:
        try:
            pool = get_pool()
            async with pool.acquire() as conn:
                await conn.fetchrow("SELECT 1")
            return {"status": "ok", "db": "sqlite"}
        except Exception:
            return {"status": "ok", "db": "sqlite-pending"}
    try:
        pool = get_pool()
        async with pool.acquire() as conn:
            await conn.fetchrow("SELECT 1")
        return {"status": "ok", "db": "postgres"}
    except Exception:
        return {"status": "ok", "db": "disconnected"}
