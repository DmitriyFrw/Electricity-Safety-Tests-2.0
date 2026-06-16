from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.errors import api_error_response
from app.support.errors import AppError


def _format_validation_errors(exc: RequestValidationError) -> str:
    parts: list[str] = []
    for err in exc.errors():
        loc = [str(x) for x in err.get("loc", ()) if x not in ("body", "query", "path")]
        msg = str(err.get("msg", "Некорректное значение"))
        if loc:
            parts.append(f"{'.'.join(loc)}: {msg}")
        else:
            parts.append(msg)
    return "; ".join(parts) if parts else "Ошибка валидации данных"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return api_error_response(
            request,
            detail=_format_validation_errors(exc),
            status_code=422,
            code="validation_error",
        )

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return api_error_response(
            request,
            detail=exc.message,
            status_code=exc.status_code,
            code=exc.error_code,
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        return api_error_response(
            request,
            detail=detail,
            status_code=exc.status_code,
            code=f"http_{exc.status_code}",
        )
