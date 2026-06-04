from __future__ import annotations

from sqlalchemy.orm import Session

from app.dto import AuditEventDTO
from app.models import Test, User
from app.policies import AccessPolicy
from app.services.security import SecurityAuditService
from app.support.errors import AppError


def require_test_edit_access(db: Session, test_id: int, user: User) -> Test:
    test = db.get(Test, test_id)
    if not test:
        raise AppError("Тест не найден", status_code=404)
    if not AccessPolicy.can_edit_test(user, test):
        SecurityAuditService.log(
            AuditEventDTO(
                action="test_edit_forbidden",
                actor_id=user.id,
                actor_username=user.username,
                success=False,
                details=f"test_id={test_id}",
            )
        )
        raise AppError(
            "Редактирование доступно только автору (Еж) или admin",
            status_code=403,
        )
    return test
