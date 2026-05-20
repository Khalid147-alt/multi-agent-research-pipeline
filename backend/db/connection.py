import json
import logging
from typing import Any, Optional

try:
    import asyncpg
except ImportError:
    asyncpg = None  # Safe on HuggingFace where asyncpg is not installed

from config import get_settings

logger = logging.getLogger(__name__)
_pool: Optional[Any] = None


async def _init_connection(conn: Any) -> None:
    await conn.set_type_codec(
        "jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog"
    )
    await conn.set_type_codec(
        "json", encoder=json.dumps, decoder=json.loads, schema="pg_catalog"
    )


async def init_db_pool() -> Any:
    global _pool
    if _pool is not None:
        return _pool
    if asyncpg is None:
        raise RuntimeError("asyncpg not installed. Use USE_SQLITE=true on HuggingFace.")
    settings = get_settings()
    _pool = await asyncpg.create_pool(
        settings.database_url,
        min_size=2,
        max_size=10,
        init=_init_connection,
    )
    return _pool


async def close_db_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


def get_pool() -> Any:
    if _pool is None:
        raise RuntimeError("DB pool not initialized.")
    return _pool


async def init_schema():
    return None
