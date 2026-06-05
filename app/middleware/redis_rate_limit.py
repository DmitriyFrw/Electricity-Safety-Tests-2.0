from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any, Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.config import get_settings

if TYPE_CHECKING:
    from redis.asyncio import Redis as AsyncRedis
else:
    try:
        from redis.asyncio import Redis as AsyncRedis
    except Exception:  # pragma: no cover
        AsyncRedis = None  # type: ignore[misc, assignment]

logger = logging.getLogger("redis-rate-limit")


class RedisRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Простейшее rate limit на Redis:
    - INCR key (ip + path)
    - expire на window_seconds при первом увеличении
    """

    def __init__(self, app: Any, *, redis_url: str):
        super().__init__(app)
        if AsyncRedis is None:
            raise RuntimeError("Redis package is not installed")
        self.redis: AsyncRedis = AsyncRedis.from_url(
            redis_url, encoding="utf-8", decode_responses=True
        )

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        settings = get_settings()
        if not settings.rate_limit_enabled or not settings.redis_url:
            return await call_next(request)

        client_host: Optional[str] = request.client.host if request.client else None
        ip = client_host or "unknown"
        path = request.url.path

        corr_id = getattr(request.state, "correlation_id", None) or request.headers.get(
            "X-Correlation-ID"
        )
        key = f"rl:{ip}:{path}"

        limit = settings.rate_limit_requests
        window = settings.rate_limit_window_seconds

        try:
            current = await self.redis.incr(key)
            if current == 1:
                await self.redis.expire(key, window)
        except Exception:
            logger.exception("Rate limit failed (corr=%s)", corr_id)
            return await call_next(request)

        remaining = max(0, limit - current)
        if current > limit:
            retry_after = await self.redis.ttl(key)
            return JSONResponse(
                status_code=429,
                content={"detail": "Слишком много запросов. Попробуйте позже."},
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": str(remaining),
                    "Retry-After": str(max(1, int(retry_after)) if retry_after is not None else 1),
                    **({"X-Correlation-ID": corr_id} if corr_id else {}),
                },
            )

        response = await call_next(request)
        response.headers.setdefault("X-RateLimit-Limit", str(limit))
        response.headers.setdefault("X-RateLimit-Remaining", str(remaining))
        return response
