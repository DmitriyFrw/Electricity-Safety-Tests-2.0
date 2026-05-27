from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


def _normalize_db_url(url: str) -> str:
    u = url.replace("postgres://", "postgresql://", 1)
    if not u:
        return u
    scheme, rest = u.split("://", 1)
    if scheme == "postgresql" and "+" not in scheme:
        return f"postgresql+psycopg://{rest}"
    return u


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


class Settings:
    database_url: str = _normalize_db_url(os.getenv("DATABASE_URL", ""))
    secret_key: str = os.getenv("SECRET_KEY", "dev-change-me-in-production")
    app_host: str = os.getenv("APP_HOST", "127.0.0.1")
    app_port: int = int(os.getenv("APP_PORT", "8000"))
    session_cookie_secure: bool = _env_bool("SESSION_COOKIE_SECURE", False)
    session_cookie_httponly: bool = _env_bool("SESSION_COOKIE_HTTPONLY", True)
    session_cookie_samesite: str = os.getenv("SESSION_COOKIE_SAMESITE", "lax").strip().lower()
    cors_origins: list[str] = [
        o.strip()
        for o in os.getenv(
            "CORS_ORIGINS",
            "http://127.0.0.1:5173,http://localhost:5173",
        ).split(",")
        if o.strip()
    ]


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    if s.session_cookie_samesite not in ("lax", "strict", "none"):
        s.session_cookie_samesite = "lax"
    return s
