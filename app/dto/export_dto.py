from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(slots=True)
class ExportRequestDTO:
    user_id: int
    test_id: int | None = None
    kind: str = "exam_results"


@dataclass(slots=True)
class ExportTaskDTO:
    task_id: str
    status: str = "pending"
    content_type: str | None = None
    filename: str | None = None
    payload: bytes | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
