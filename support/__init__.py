"""Вспомогательные модули домена (без HTTP и ORM-сессий в публичном API)."""

from app.support.errors import AppError

__all__ = ["AppError"]
