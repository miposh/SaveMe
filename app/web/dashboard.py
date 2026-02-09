import hashlib
import logging
import pathlib
import secrets
import time

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_config
from app.infrastructure.database.connection.connect_to_pg import get_pg_pool
from app.infrastructure.database.connection.psycopg_connection import PsycopgConnection
from app.infrastructure.database.db import DB

logger = logging.getLogger(__name__)

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "web" / "templates"
STATIC_DIR = PROJECT_ROOT / "web" / "static"

_tokens: dict[str, float] = {}
_failed_attempts: dict[str, list[float]] = {}
_db_pool = None

SESSION_TTL = 3600
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_SECONDS = 300


async def _get_db() -> DB:
    global _db_pool
    config = get_config()
    if _db_pool is None:
        _db_pool = await get_pg_pool(
            db_name=config.postgres.db,
            host=config.postgres.host,
            port=config.postgres.port,
            user=config.postgres.user,
            password=config.postgres.password,
            min_size=1,
            max_size=3,
        )
    raw_conn = await _db_pool.getconn()
    try:
        conn = PsycopgConnection(raw_conn)
        return DB(conn)
    finally:
        await _db_pool.putconn(raw_conn)


def _verify_token(token: str) -> bool:
    created = _tokens.get(token)
    if not created:
        return False
    if time.time() - created > SESSION_TTL:
        _tokens.pop(token, None)
        return False
    return True


def _is_locked_out(ip: str) -> bool:
    attempts = _failed_attempts.get(ip, [])
    now = time.time()
    recent = [t for t in attempts if now - t < LOCKOUT_SECONDS]
    _failed_attempts[ip] = recent
    return len(recent) >= MAX_FAILED_ATTEMPTS


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        public_paths = ["/login", "/api/login", "/static", "/health"]
        if any(request.url.path.startswith(p) for p in public_paths):
            return await call_next(request)

        token = request.cookies.get("auth_token")
        if not token or not _verify_token(token):
            if request.url.path.startswith("/api/"):
                raise HTTPException(status_code=401, detail="Unauthorized")
            return RedirectResponse(url="/login", status_code=302)

        return await call_next(request)


app = FastAPI(title="SaveMe Dashboard", version="2.0.0")

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AuthMiddleware)

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


class LoginRequest(BaseModel):
    username: str = Field(...)
    password: str = Field(...)


class BlockRequest(BaseModel):
    user_id: int = Field(..., gt=0)
    reason: str | None = Field(default=None, max_length=120)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/api/login")
async def api_login(payload: LoginRequest, request: Request):
    config = get_config()
    client_ip = request.client.host if request.client else "unknown"

    if _is_locked_out(client_ip):
        raise HTTPException(status_code=429, detail="Too many attempts. Try later.")

    if (
        payload.username == config.dashboard.username
        and payload.password == config.dashboard.password
    ):
        token = secrets.token_hex(32)
        _tokens[token] = time.time()
        response = Response(
            content='{"status": "ok"}', media_type="application/json"
        )
        response.set_cookie(
            key="auth_token",
            value=token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=SESSION_TTL,
        )
        return response

    _failed_attempts.setdefault(client_ip, []).append(time.time())
    raise HTTPException(status_code=401, detail="Invalid credentials")


@app.post("/api/logout")
async def api_logout(request: Request):
    token = request.cookies.get("auth_token")
    if token:
        _tokens.pop(token, None)
    response = Response(content='{"status":"ok"}', media_type="application/json")
    response.delete_cookie("auth_token")
    return response


@app.get("/", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "title": "Bot statistics", "config": {}},
    )


@app.get("/api/stats")
async def api_stats():
    config = get_config()
    pool = await _ensure_pool(config)
    async with pool.connection() as raw_conn:
        conn = PsycopgConnection(raw_conn)
        db = DB(conn)

        total_users = await db.users.get_users_count()
        total_downloads = await db.downloads.get_total_count()
        today_downloads = await db.downloads.get_count_by_period("day")
        week_downloads = await db.downloads.get_count_by_period("week")
        new_users_today = await db.users.get_users_by_period("day")
        new_users_week = await db.users.get_users_by_period("week")

        return {
            "total_users": total_users,
            "total_downloads": total_downloads,
            "today_downloads": today_downloads,
            "week_downloads": week_downloads,
            "new_users_today": new_users_today,
            "new_users_week": new_users_week,
        }


@app.get("/api/top-domains")
async def api_top_domains(limit: int = 10):
    config = get_config()
    pool = await _ensure_pool(config)
    async with pool.connection() as raw_conn:
        conn = PsycopgConnection(raw_conn)
        db = DB(conn)
        result = await db.downloads.get_top_domains(limit)
        return result.data if result else []


@app.get("/api/user-history")
async def api_user_history(user_id: int = Query(..., gt=0), limit: int = 100):
    config = get_config()
    pool = await _ensure_pool(config)
    async with pool.connection() as raw_conn:
        conn = PsycopgConnection(raw_conn)
        db = DB(conn)
        result = await db.downloads.get_by_user(user_id, limit)
        return result.data if result else []


@app.post("/api/block-user")
async def api_block_user(payload: BlockRequest):
    config = get_config()
    pool = await _ensure_pool(config)
    async with pool.connection() as raw_conn:
        conn = PsycopgConnection(raw_conn)
        db = DB(conn)
        await db.users.ban_user(payload.user_id, reason=payload.reason)
        return {"status": "ok"}


@app.post("/api/unblock-user")
async def api_unblock_user(payload: BlockRequest):
    config = get_config()
    pool = await _ensure_pool(config)
    async with pool.connection() as raw_conn:
        conn = PsycopgConnection(raw_conn)
        db = DB(conn)
        await db.users.unban_user(payload.user_id)
        return {"status": "ok"}


@app.get("/health")
async def health():
    return {"status": "ok"}


async def _ensure_pool(config):
    global _db_pool
    if _db_pool is None:
        _db_pool = await get_pg_pool(
            db_name=config.postgres.db,
            host=config.postgres.host,
            port=config.postgres.port,
            user=config.postgres.user,
            password=config.postgres.password,
            min_size=1,
            max_size=3,
        )
    return _db_pool
