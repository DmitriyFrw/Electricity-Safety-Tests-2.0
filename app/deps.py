from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Test, User
from app.roles import can_create_tests, can_edit_test


def get_current_user_optional(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> User | None:
    uid = request.session.get("user_id")
    if not uid:
        return None
    return db.get(User, int(uid))


def login_required(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> User:
    user = get_current_user_optional(request, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется вход в систему",
        )
    return user


def test_editor_required(user: Annotated[User, Depends(login_required)]) -> User:
    if not can_create_tests(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Создание и редактирование тестов доступно только ролям Еж и admin",
        )
    return user


def require_test_edit_access(db: Session, test_id: int, user: User) -> Test:
    test = db.get(Test, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Тест не найден")
    if not can_edit_test(user, test):
        raise HTTPException(
            status_code=403,
            detail="Редактирование доступно только автору (Еж) или admin",
        )
    return test
