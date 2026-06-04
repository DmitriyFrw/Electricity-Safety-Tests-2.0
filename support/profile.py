from __future__ import annotations

from app.models import User
from app.support.errors import AppError


def require_profile_complete(user: User, *, message: str | None = None) -> None:
    if user.full_name and user.birth_date and user.job_title:
        return
    raise AppError(
        message
        or "У пользователя Кот не заполнены ФИО, дата рождения или должность в профиле",
        status_code=400,
    )
