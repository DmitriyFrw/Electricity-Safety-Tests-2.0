from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from cachetools import TTLCache

from app.config import get_settings

P = ParamSpec("P")
R = TypeVar("R")

_caches: dict[str, TTLCache] = {}


def _get_cache(name: str) -> TTLCache:
    if name not in _caches:
        ttl = get_settings().cache_ttl_seconds
        _caches[name] = TTLCache(maxsize=128, ttl=ttl)
    return _caches[name]


def cached(name: str, key_fn: Callable[P, str] | None = None):
    """TTL-кэш для результатов сервисов (мануалы, справочники)."""

    def decorator(fn: Callable[P, R]) -> Callable[P, R]:
        @wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            cache = _get_cache(name)
            key = key_fn(*args, **kwargs) if key_fn else "default"
            if key in cache:
                return cache[key]  # type: ignore[no-any-return]
            result = fn(*args, **kwargs)
            cache[key] = result
            return result

        return wrapper

    return decorator


def invalidate_cache(name: str) -> None:
    cache = _caches.get(name)
    if cache is not None:
        cache.clear()
