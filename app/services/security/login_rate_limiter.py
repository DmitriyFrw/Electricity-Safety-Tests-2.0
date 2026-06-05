from __future__ import annotations

from cachetools import TTLCache

from app.config import get_settings


class LoginRateLimiter:
    _cache: TTLCache[str, int] = TTLCache(maxsize=50_000, ttl=300)
    _current_ttl: int = 300

    @classmethod
    def _ttl(cls) -> int:
        return get_settings().login_rate_limit_window_seconds

    @classmethod
    def _limit(cls) -> int:
        return get_settings().login_rate_limit_attempts

    @classmethod
    def _key(cls, username: str, ip: str | None) -> str:
        return f"{username.lower().strip()}::{ip or 'unknown'}"

    @classmethod
    def _ensure_cache(cls) -> None:
        ttl = cls._ttl()
        if ttl != cls._current_ttl:
            cls._cache = TTLCache(maxsize=50_000, ttl=ttl)
            cls._current_ttl = ttl

    @classmethod
    def is_blocked(cls, *, username: str, ip: str | None) -> bool:
        cls._ensure_cache()
        return int(cls._cache.get(cls._key(username, ip), 0)) >= cls._limit()

    @classmethod
    def register_failure(cls, *, username: str, ip: str | None) -> int:
        cls._ensure_cache()
        key = cls._key(username, ip)
        current = int(cls._cache.get(key, 0)) + 1
        cls._cache[key] = current
        return current

    @classmethod
    def reset(cls, *, username: str, ip: str | None) -> None:
        cls._cache.pop(cls._key(username, ip), None)
