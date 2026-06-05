from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.deps import login_required
from app.database import get_db
from app.models import User


@dataclass(frozen=True, slots=True)
class AuthenticatedDb:
    """Группировка частых зависимостей API (аналог «тонкого» service container)."""

    db: Session
    user: User


def get_authenticated_db(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
) -> AuthenticatedDb:
    return AuthenticatedDb(db=db, user=user)
