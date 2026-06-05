from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import api_router
from app.api.handlers import register_exception_handlers
from app.config import get_settings
from app.middleware.correlation_id import CorrelationIdMiddleware
from app.middleware.redis_rate_limit import RedisRateLimitMiddleware
from app.session_middleware import AppSessionMiddleware
from app.csrf import CSRFMiddleware, CSRF_HEADER
from app.database import Base, engine

settings = get_settings()
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    if settings.auto_create_schema:
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Развивайся — API",
    description="REST API платформы подготовки и сдачи экзамена по электробезопасности.",
    version="0.6.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "auth", "description": "Регистрация, вход, CSRF, сессия"},
        {"name": "tests", "description": "Тесты, тренировка, экзамен, протоколы"},
        {"name": "profile", "description": "Профиль и асинхронный экспорт"},
        {"name": "dashboard", "description": "Личный кабинет"},
        {"name": "manuals", "description": "Нормативные документы"},
        {"name": "admin", "description": "Администрирование пользователей"},
    ],
)
register_exception_handlers(app)

# Порядок add_middleware: последний добавленный — внешний (выполняется первым на запрос).
# Нужно: CORS → Session → CSRF → … → приложение (иначе CSRF/роуты падают на request.session).
if settings.rate_limit_enabled and settings.redis_url:
    try:
        app.add_middleware(RedisRateLimitMiddleware, redis_url=settings.redis_url)
    except Exception as e:
        import logging

        logging.getLogger("app").warning("Rate limit disabled: %s", e)

app.add_middleware(CSRFMiddleware)
app.add_middleware(
    AppSessionMiddleware,
    secret_key=settings.secret_key,
    session_cookie="exam_session",
    https_only=settings.session_cookie_secure,
    httponly=settings.session_cookie_httponly,
    same_site=settings.session_cookie_samesite,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", CSRF_HEADER],
    expose_headers=[CSRF_HEADER, "X-Correlation-ID"],
)

# Снаружи всего стека — заголовок X-Correlation-ID и на ответах CSRF/ошибок middleware.
app.add_middleware(CorrelationIdMiddleware)

app.include_router(api_router)

legacy_static = Path(__file__).resolve().parent / "static"
if legacy_static.is_dir():
    app.mount("/static", StaticFiles(directory=str(legacy_static)), name="static")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


if FRONTEND_DIST.is_dir():

    @app.get("/")
    def spa_index() -> FileResponse:
        return FileResponse(FRONTEND_DIST / "index.html")

    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str) -> FileResponse:
        if full_path.startswith("api"):
            raise HTTPException(status_code=404)
        candidate = FRONTEND_DIST / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")
