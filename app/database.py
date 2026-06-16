from __future__ import annotations

from collections.abc import Generator
from typing import Any

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def _get_database_url() -> str:
    url = get_settings().database_url
    if not url:
        raise RuntimeError(
            "Задайте DATABASE_URL в .env (см. .env.example). "
            "Пример: postgresql+psycopg://user:pass@localhost:5432/exam_tests"
        )
    return url


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(_get_database_url(), pool_pre_ping=True)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _session_factory


class _LazyEngine:
    """Отложенное создание engine — импорт app.main возможен без DATABASE_URL."""

    def __getattr__(self, name: str) -> Any:
        return getattr(get_engine(), name)

    def __repr__(self) -> str:
        return repr(get_engine())


engine = _LazyEngine()


class _SessionLocal:
    def __call__(self) -> Session:
        return get_session_factory()()


SessionLocal = _SessionLocal()


def get_db() -> Generator[Session, None, None]:
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()
