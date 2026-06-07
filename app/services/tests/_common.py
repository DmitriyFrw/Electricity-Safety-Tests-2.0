from __future__ import annotations

from sqlalchemy.orm import Session

from app.constants import ROLE_KOT
from app.models import Test, User
from app.repositories import TestRepository
from app.support.errors import AppError
from app.support.safety_groups import effective_safety_group
from app.support.validation import test_is_ready_to_take


def get_test_or_raise(db: Session, test_id: int) -> Test:
    return TestRepository.get_full_or_raise(db, test_id)


def require_test_group_access(test: Test, user: User) -> None:
    if user.role == ROLE_KOT and test.safety_group != effective_safety_group(user):
        raise AppError(
            "Этот тест не соответствует вашей группе по электробезопасности",
            status_code=403,
        )


def require_test_ready(test: Test, user: User, db: Session) -> None:
    require_test_group_access(test, user)
    if not test.published:
        if user.id == test.author_id:
            raise AppError(
                "Тест ещё не опубликован. Нажмите «Тест готов» в конструкторе",
                status_code=400,
            )
        raise AppError("Тест недоступен для сдачи", status_code=400)
    if not test_is_ready_to_take(db, test):
        if user.id == test.author_id:
            raise AppError(
                "Нет готовых билетов: заполните хотя бы один билет с 10 вопросами",
                status_code=400,
            )
        raise AppError("Тест недоступен для сдачи", status_code=400)
