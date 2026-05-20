import logging
import re
from pathlib import Path
from typing import Optional

import aiosqlite

logger = logging.getLogger(__name__)
DB_PATH = Path("/tmp/research_pipeline.db")
_pool = None  # shim — aiosqlite opens per-call

_PLACEHOLDER_RE = re.compile(r"\$\d+")


def _translate(sql: str) -> str:
    return _PLACEHOLDER_RE.sub("?", sql)


class _SqlitePool:
    """Minimal asyncpg-compatible pool shim for aiosqlite."""

    def acquire(self):
        return _SqliteConn()


class _SqliteConn:
    def __init__(self):
        self._conn: Optional[aiosqlite.Connection] = None

    async def __aenter__(self):
        self._conn = await aiosqlite.connect(DB_PATH)
        self._conn.row_factory = aiosqlite.Row
        return self

    async def __aexit__(self, *args):
        if self._conn:
            await self._conn.commit()
            await self._conn.close()

    async def execute(self, sql: str, *args):
        await self._conn.execute(_translate(sql), args if args else ())

    async def fetchrow(self, sql: str, *args):
        async with self._conn.execute(_translate(sql), args if args else ()) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None

    async def fetch(self, sql: str, *args):
        async with self._conn.execute(_translate(sql), args if args else ()) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def init_db_pool():
    global _pool
    _pool = _SqlitePool()
    logger.info(f"SQLite pool shim initialized at {DB_PATH}")
    return _pool


async def close_db_pool():
    global _pool
    _pool = None


def get_pool():
    if _pool is None:
        raise RuntimeError("SQLite pool not initialized.")
    return _pool


async def init_schema():
    schema_path = Path(__file__).parent / "sqlite_schema.sql"
    async with aiosqlite.connect(DB_PATH) as conn:
        schema = schema_path.read_text()
        await conn.executescript(schema)
        await conn.commit()
    logger.info(f"SQLite schema applied at {DB_PATH}")
