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


class Settings:
    database_url: str = _normalize_db_url(os.getenv("DATABASE_URL", ""))
    secret_key: str = os.getenv("SECRET_KEY", "dev-change-me-in-production")
    app_host: str = os.getenv("APP_HOST", "127.0.0.1")
    app_port: int = int(os.getenv("APP_PORT", "8000"))
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
    return Settings()
