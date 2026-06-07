from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Test, User
from app.policies import AccessPolicy
from app.support.errors import AppError


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


def admin_required(user: Annotated[User, Depends(login_required)]) -> User:
    if not AccessPolicy.can_manage_users(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Раздел администрирования доступен только роли admin",
        )
    return user


def staff_required(user: Annotated[User, Depends(login_required)]) -> User:
    if not AccessPolicy.can_manage_safety_groups(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Раздел доступен только ролям admin и Еж",
        )
    return user


def test_editor_required(user: Annotated[User, Depends(login_required)]) -> User:
    if not AccessPolicy.can_create_tests(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Создание и редактирование тестов доступно только ролям Еж и admin",
        )
    return user


def wiki_editor_required(user: Annotated[User, Depends(login_required)]) -> User:
    if not AccessPolicy.can_edit_wiki(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Редактирование вики доступно только ролям admin и Еж",
        )
    return user


def require_test_edit_access(db: Session, test_id: int, user: User) -> Test:
    from app.policies.test_edit import require_test_edit_access as _require

    try:
        return _require(db, test_id, user)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e
