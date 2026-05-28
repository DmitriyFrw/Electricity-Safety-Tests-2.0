from __future__ import annotations

import logging

from app.dto import AuditEventDTO

logger = logging.getLogger("security-audit")


class SecurityAuditService:
    @staticmethod
    def log(event: AuditEventDTO) -> None:
        logger.warning(
            "audit action=%s success=%s actor_id=%s actor=%s ip=%s details=%s",
            event.action,
            event.success,
            event.actor_id,
            event.actor_username,
            event.ip,
            event.details,
        )
