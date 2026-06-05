from __future__ import annotations

import contextvars
import uuid

from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


correlation_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "correlation_id", default=None
)


def get_correlation_id() -> str | None:
    return correlation_id_ctx.get()


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Добавляет заголовок `X-Correlation-ID` в ответы и кладёт ID в `request.state`.
    Нужен для трассировки запросов (в т.ч. при rate limiting).
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        corr_id = request.headers.get("X-Correlation-ID") or uuid.uuid4().hex
        request.state.correlation_id = corr_id
        correlation_id_ctx.set(corr_id)

        response = await call_next(request)
        response.headers["X-Correlation-ID"] = corr_id
        return response

