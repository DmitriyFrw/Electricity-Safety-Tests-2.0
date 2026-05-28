from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AuditEventDTO:
    action: str
    actor_id: int | None
    actor_username: str | None
    success: bool
    ip: str | None = None
    details: str | None = None
