from __future__ import annotations

ERROR_EXAM_TICKET_TIME_EXPIRED = "exam_ticket_time_expired"
EXAM_TICKET_TIME_EXPIRED_MESSAGE = "Время на билет истекло"


class ExamTicketTimeExpiredError(ValueError):
    """Билет закрыт по таймеру."""


class AppError(Exception):
    """Бизнес-ошибка с HTTP-кодом (маппится в exception handler API)."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 400,
        error_code: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
