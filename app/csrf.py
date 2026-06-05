from __future__ import annotations

import secrets

import uuid

from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

CSRF_SESSION_KEY = "csrf_token"
CSRF_HEADER = "X-CSRF-Token"
SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})

# Без проверки CSRF (только безопасные методы или служебные пути)
CSRF_EXEMPT_EXACT = frozenset({"/api/health", "/api/auth/csrf"})
CSRF_EXEMPT_PREFIXES = ("/docs", "/openapi.json", "/redoc")


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def get_or_create_csrf_token(request: Request) -> str:
    token = request.session.get(CSRF_SESSION_KEY)
    if not token or not isinstance(token, str):
        token = generate_csrf_token()
        request.session[CSRF_SESSION_KEY] = token
    return token


def rotate_csrf_token(request: Request) -> str:
    token = generate_csrf_token()
    request.session[CSRF_SESSION_KEY] = token
    return token


def validate_csrf(request: Request) -> bool:
    expected = request.session.get(CSRF_SESSION_KEY)
    if not expected or not isinstance(expected, str):
        return False
    provided = request.headers.get(CSRF_HEADER)
    if not provided:
        return False
    return secrets.compare_digest(provided, expected)


def _path_exempt(path: str) -> bool:
    if path in CSRF_EXEMPT_EXACT:
        return True
    return any(path.startswith(prefix) for prefix in CSRF_EXEMPT_PREFIXES)


class CSRFMiddleware(BaseHTTPMiddleware):
    """Проверка заголовка X-CSRF-Token для POST/PUT/PATCH/DELETE (токен в сессии)."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if _path_exempt(request.url.path) or request.method in SAFE_METHODS:
            return await call_next(request)
        if not validate_csrf(request):
            corr_id = getattr(request.state, "correlation_id", None) or uuid.uuid4().hex
            return JSONResponse(
                status_code=403,
                content={"detail": "Неверный или отсутствующий CSRF-токен"},
                headers={"X-Correlation-ID": corr_id},
            )
        return await call_next(request)
