from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.dto.base import ValidatedDTO

ExportKind = Literal["exam_results", "protocol"]
ExportStatus = Literal["pending", "running", "done", "failed"]


class ExportRequestDTO(ValidatedDTO):
    user_id: int = Field(gt=0)
    test_id: int | None = Field(default=None, gt=0)
    kind: ExportKind = "exam_results"


class ExportTaskDTO(BaseModel):
    """Мутабельная задача экспорта (обновляется через ExportTaskStore.patch)."""

    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(min_length=8, max_length=64)
    owner_user_id: int = Field(gt=0)
    status: str = "pending"
    content_type: str | None = None
    filename: str | None = Field(default=None, max_length=255)
    payload: bytes | None = None
    error: str | None = Field(default=None, max_length=2000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("created_at")
    @classmethod
    def ensure_utc_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
