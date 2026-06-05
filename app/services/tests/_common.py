from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Test, User
from app.repositories import TestRepository
from app.support.errors import AppError
from app.support.validation import test_is_ready_loaded, test_is_ready_to_take


def get_test_or_raise(db: Session, test_id: int) -> Test:
    return TestRepository.get_full_or_raise(db, test_id)


def require_test_ready(test: Test, user: User, db: Session) -> None:
    ready = test_is_ready_loaded(test) if test.tickets else test_is_ready_to_take(db, test)
    if not ready:
        if user.id == test.author_id:
            raise AppError("Тест ещё не заполнен полностью", status_code=400)
        raise AppError("Тест недоступен для сдачи", status_code=400)
