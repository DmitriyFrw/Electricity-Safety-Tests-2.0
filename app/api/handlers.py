from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

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
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": _format_validation_errors(exc)})

    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})
