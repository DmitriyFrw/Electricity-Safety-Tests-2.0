from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ValidatedDTO(BaseModel):
    """Внутренний DTO с валидацией (аналог Form Request для границ сервисов)."""

    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)
