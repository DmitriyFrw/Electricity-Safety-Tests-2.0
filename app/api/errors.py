from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from app.middleware.correlation_id import get_correlation_id


def correlation_id_for_request(request: Request) -> str | None:
    return getattr(request.state, "correlation_id", None) or get_correlation_id()


def api_error_body(
    request: Request,
    *,
    detail: str,
    code: str | None = None,
) -> dict[str, str | None]:
    return {
        "detail": detail,
        "code": code,
        "correlation_id": correlation_id_for_request(request),
    }


def api_error_response(
    request: Request,
    *,
    detail: str,
    status_code: int,
    code: str | None = None,
) -> JSONResponse:
    corr_id = correlation_id_for_request(request)
    headers = {"X-Correlation-ID": corr_id} if corr_id else {}
    return JSONResponse(
        status_code=status_code,
        content=api_error_body(request, detail=detail, code=code),
        headers=headers,
    )
