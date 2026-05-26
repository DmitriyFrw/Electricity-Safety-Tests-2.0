from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User


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
