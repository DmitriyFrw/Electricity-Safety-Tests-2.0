from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings.sources import NoDecode
from typing import Annotated


def _normalize_db_url(url: str) -> str:
    # postgres:// -> postgresql+psycopg:// (psycopg v3)
    u = url.replace("postgres://", "postgresql://", 1)
    if not u:
        return u
    scheme, rest = u.split("://", 1)
    if scheme == "postgresql" and "+" not in scheme:
        return f"postgresql+psycopg://{rest}"
    return u


ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(default="", alias="DATABASE_URL")
    secret_key: str = Field(default="dev-change-me-in-production", alias="SECRET_KEY")
    app_host: str = Field(default="127.0.0.1", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")

    session_cookie_secure: bool = Field(default=False, alias="SESSION_COOKIE_SECURE")
    session_cookie_httponly: bool = Field(default=True, alias="SESSION_COOKIE_HTTPONLY")
    session_cookie_samesite: Literal["lax", "strict", "none"] = Field(
        default="lax", alias="SESSION_COOKIE_SAMESITE"
    )

    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://127.0.0.1:5173", "http://localhost:5173"],
        alias="CORS_ORIGINS",
    )

    # Rate limiting (Redis)
    redis_url: str = Field(default="", alias="REDIS_URL")
    rate_limit_enabled: bool = Field(default=False, alias="RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(default=60, alias="RATE_LIMIT_REQUESTS")
    rate_limit_window_seconds: int = Field(default=60, alias="RATE_LIMIT_WINDOW_SECONDS")

    # Безопасность и производительность
    bcrypt_rounds: int = Field(default=12, alias="BCRYPT_ROUNDS", ge=4, le=31)
    cache_ttl_seconds: int = Field(default=300, alias="CACHE_TTL_SECONDS", ge=0)
    test_list_cache_ttl_seconds: int = Field(
        default=3600, alias="TEST_LIST_CACHE_TTL_SECONDS", ge=0
    )
    login_rate_limit_attempts: int = Field(default=5, alias="LOGIN_RATE_LIMIT_ATTEMPTS", ge=1)
    login_rate_limit_window_seconds: int = Field(
        default=300, alias="LOGIN_RATE_LIMIT_WINDOW_SECONDS", ge=1
    )
    auto_create_schema: bool = Field(default=True, alias="AUTO_CREATE_SCHEMA")
    export_task_ttl_seconds: int = Field(default=3600, alias="EXPORT_TASK_TTL_SECONDS", ge=60)

    @field_validator("database_url", mode="before")
    @classmethod
    def _v_normalize_db_url(cls, v: object) -> object:
        if not isinstance(v, str):
            return v
        return _normalize_db_url(v.strip())

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _v_parse_cors_origins(cls, v: object) -> object:
        # Support "a,b,c" format from env
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
