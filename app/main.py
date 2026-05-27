from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.api import api_router
from app.config import get_settings
from app.session_middleware import AppSessionMiddleware
from app.csrf import CSRFMiddleware, CSRF_HEADER
from app.database import Base, engine

settings = get_settings()
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Развивайся — API", lifespan=lifespan)
app.add_middleware(
    AppSessionMiddleware,
    secret_key=settings.secret_key,
    session_cookie="exam_session",
    https_only=settings.session_cookie_secure,
    httponly=settings.session_cookie_httponly,
    same_site=settings.session_cookie_samesite,  # type: ignore[arg-type]
)
app.add_middleware(CSRFMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", CSRF_HEADER],
    expose_headers=[CSRF_HEADER],
)

app.include_router(api_router)

legacy_static = Path(__file__).resolve().parent / "static"
if legacy_static.is_dir():
    app.mount("/static", StaticFiles(directory=str(legacy_static)), name="static")


@app.get("/api/health")
def health():
    return {"status": "ok"}


if FRONTEND_DIST.is_dir():

    @app.get("/")
    def spa_index():
        return FileResponse(FRONTEND_DIST / "index.html")

    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str):
        if full_path.startswith("api"):
            raise HTTPException(status_code=404)
        candidate = FRONTEND_DIST / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")
