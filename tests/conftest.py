from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path
from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient


def _configure_test_env() -> Path:
    db_path = Path(tempfile.gettempdir()) / f"exam_tests_pytest_{uuid.uuid4().hex}.db"
    os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{db_path}"
    os.environ["SECRET_KEY"] = os.environ.get("SECRET_KEY", "test-secret")
    os.environ["APP_HOST"] = os.environ.get("APP_HOST", "127.0.0.1")
    os.environ["APP_PORT"] = os.environ.get("APP_PORT", "8000")
    os.environ["CORS_ORIGINS"] = os.environ.get("CORS_ORIGINS", "http://localhost:5173")
    os.environ["SESSION_COOKIE_SECURE"] = os.environ.get("SESSION_COOKIE_SECURE", "false")
    os.environ["SESSION_COOKIE_HTTPONLY"] = os.environ.get("SESSION_COOKIE_HTTPONLY", "true")
    os.environ["SESSION_COOKIE_SAMESITE"] = os.environ.get("SESSION_COOKIE_SAMESITE", "lax")

    # For CI/tests we keep rate limiting off by default.
    os.environ["RATE_LIMIT_ENABLED"] = os.environ.get("RATE_LIMIT_ENABLED", "false")
    os.environ["REDIS_URL"] = os.environ.get("REDIS_URL", "")
    return db_path


_DB_PATH = _configure_test_env()

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _create_schema():
    Base.metadata.create_all(bind=engine)
    yield

    # Cleanup db file (sqlite only).
    try:
        _DB_PATH.unlink(missing_ok=True)
    except Exception:
        pass


@pytest.fixture()
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


async def get_csrf_token(client: AsyncClient) -> str:
    r = await client.get("/api/auth/csrf")
    r.raise_for_status()
    return r.json()["csrf_token"]


async def register_user(
    client: AsyncClient,
    *,
    username: str,
    password: str = "password123",
) -> dict:
    csrf = await get_csrf_token(client)
    r = await client.post(
        "/api/auth/register",
        json={"username": username, "password": password, "password2": password},
        headers={"X-CSRF-Token": csrf},
    )
    r.raise_for_status()
    return r.json()

