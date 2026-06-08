from __future__ import annotations

from typing import TYPE_CHECKING

from cachetools import TTLCache

from app.config import get_settings

if TYPE_CHECKING:
    import redis


class LoginRateLimiter:
    _cache: TTLCache[str, int] = TTLCache(maxsize=50_000, ttl=300)
    _current_ttl: int = 300
    _redis: redis.Redis | None = None

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
    def _redis_key(cls, username: str, ip: str | None) -> str:
        return f"login_fail:{cls._key(username, ip)}"

    @classmethod
    def _use_redis(cls) -> bool:
        return bool(get_settings().redis_url)

    @classmethod
    def _redis_client(cls) -> redis.Redis:
        if cls._redis is None:
            import redis as redis_lib

            cls._redis = redis_lib.from_url(get_settings().redis_url, decode_responses=True)
        return cls._redis

    @classmethod
    def _ensure_cache(cls) -> None:
        ttl = cls._ttl()
        if ttl != cls._current_ttl:
            cls._cache = TTLCache(maxsize=50_000, ttl=ttl)
            cls._current_ttl = ttl

    @classmethod
    def is_blocked(cls, *, username: str, ip: str | None) -> bool:
        if cls._use_redis():
            count = int(cls._redis_client().get(cls._redis_key(username, ip)) or 0)
            return count >= cls._limit()
        cls._ensure_cache()
        return int(cls._cache.get(cls._key(username, ip), 0)) >= cls._limit()

    @classmethod
    def register_failure(cls, *, username: str, ip: str | None) -> int:
        if cls._use_redis():
            key = cls._redis_key(username, ip)
            client = cls._redis_client()
            current = int(client.incr(key))
            if current == 1:
                client.expire(key, cls._ttl())
            return current
        cls._ensure_cache()
        key = cls._key(username, ip)
        current = int(cls._cache.get(key, 0)) + 1
        cls._cache[key] = current
        return current

    @classmethod
    def reset(cls, *, username: str, ip: str | None) -> None:
        if cls._use_redis():
            cls._redis_client().delete(cls._redis_key(username, ip))
            return
        cls._cache.pop(cls._key(username, ip), None)
