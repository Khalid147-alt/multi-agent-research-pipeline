import logging
import os
import sys
from contextlib import asynccontextmanager

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from api.health import router as health_router
from api.research import router as research_router
from api.websocket import router as ws_router
from config import get_settings
from db.adapter import USE_SQLITE, close_db_pool, init_db_pool, init_schema

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s | %(message)s")
logger = logging.getLogger("main")


_DEFAULT_ORIGINS = (
    "https://research-pipeline-eta.vercel.app,"
    "http://localhost:5173,"
    "http://127.0.0.1:5173"
)


def _allowed_origins() -> list[str]:
    raw = os.environ.get("ALLOWED_ORIGINS", _DEFAULT_ORIGINS)
    return [o.strip() for o in raw.split(",") if o.strip()]


_PLACEHOLDER_SUBSTRINGS = ("your_", "changeme", "placeholder", "xxxx")


def _looks_like_placeholder(value: str) -> bool:
    v = (value or "").lower()
    return (not v) or any(s in v for s in _PLACEHOLDER_SUBSTRINGS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info(f"Starting (env={settings.environment}, use_sqlite={USE_SQLITE})")

    if settings.environment == "production":
        if _looks_like_placeholder(settings.gemini_api_key):
            raise RuntimeError(
                "GEMINI_API_KEY looks like a placeholder — refusing to start."
            )
        if _looks_like_placeholder(settings.tavily_api_key):
            raise RuntimeError(
                "TAVILY_API_KEY looks like a placeholder — refusing to start."
            )

    if USE_SQLITE:
        await init_schema()
        logger.info("SQLite schema applied")

    await init_db_pool()
    logger.info("DB pool ready")
    app.state.recent_sessions = {}
    yield
    await close_db_pool()


# ---- rate limiter ----------------------------------------------------------

limiter = Limiter(key_func=get_remote_address, default_limits=[])


# ---- security-headers middleware -------------------------------------------

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # HSTS is harmless behind HF's HTTPS proxy and matters in prod.
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
        )
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault(
            "Referrer-Policy", "strict-origin-when-cross-origin"
        )
        response.headers.setdefault("Permissions-Policy", "geolocation=(), camera=(), microphone=()")
        # CSP is intentionally narrow; this is a JSON API, no browser UI here.
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
        )
        return response


# ---- app ------------------------------------------------------------------

app = FastAPI(title="Research Pipeline", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

_resolved_origins = _allowed_origins()
logger.info(f"CORS allow_origins resolved to: {_resolved_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_resolved_origins,
    allow_origin_regex=None,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
    max_age=600,
)


# Explicit per-route limits ---------------------------------------------------
# We attach these via decorator wrappers around the imported routers' endpoints.
# slowapi's Limiter checks request.state, so we just install rate limits as
# global rules and let the routers handle the logic.

# Friendlier 429 payload
@app.exception_handler(RateLimitExceeded)
async def _custom_rate_limit(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Too many requests. Please slow down.",
            "limit": str(exc.detail),
        },
    )


app.include_router(health_router)
app.include_router(research_router)
app.include_router(ws_router)


# Per-route rate limits via app.state.limiter — applied after include_router so
# we can pull the underlying functions and re-wrap with explicit limits.
# This is slowapi's idiomatic way to set per-endpoint limits on already-mounted
# routers when you can't decorate the source.

from api import research as _research_mod  # noqa: E402
from api import websocket as _ws_mod  # noqa: E402

# Decorate the route handlers after registration. slowapi reads request.state
# inside the middleware, and the decorator just registers the rule.
limiter.limit("5/15minutes")(_research_mod.start_research)
limiter.limit("60/minute")(_research_mod.get_report)
limiter.limit("60/minute")(_research_mod.get_report_pdf)
limiter.limit("60/minute")(_research_mod.get_history)
