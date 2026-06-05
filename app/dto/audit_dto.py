from __future__ import annotations

from typing import Literal

from pydantic import Field

from app.dto.base import ValidatedDTO

AuditAction = Literal["login", "register", "logout", "test_edit_forbidden"]


class AuditEventDTO(ValidatedDTO):
    action: AuditAction
    actor_id: int | None = Field(default=None, ge=1)
    actor_username: str | None = Field(default=None, max_length=64)
    success: bool
    ip: str | None = Field(default=None, max_length=45)
    details: str | None = Field(default=None, max_length=500)
