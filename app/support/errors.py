from __future__ import annotations


class AppError(Exception):
    """Бизнес-ошибка с HTTP-кодом (маппится в exception handler API)."""

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
