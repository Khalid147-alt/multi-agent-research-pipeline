"""
Database adapter — dispatches to asyncpg (local) or aiosqlite (HuggingFace).
All other modules import from db.adapter only.
"""
from __future__ import annotations

import os


def _use_sqlite() -> bool:
    return os.environ.get("USE_SQLITE", "false").lower() in {"1", "true", "yes"}


if _use_sqlite():
    from db.sqlite_connection import (  # noqa: F401
        close_db_pool,
        get_pool,
        init_db_pool,
        init_schema,
    )
else:
    try:
        from db.connection import (  # noqa: F401
            close_db_pool,
            get_pool,
            init_db_pool,
            init_schema,
        )
    except ImportError:
        # asyncpg not installed (HF environment) — fall back to SQLite
        from db.sqlite_connection import (  # noqa: F401
            close_db_pool,
            get_pool,
            init_db_pool,
            init_schema,
        )

USE_SQLITE = _use_sqlite()
