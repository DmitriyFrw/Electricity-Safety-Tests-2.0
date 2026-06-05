from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import User
from app.support.errors import AppError


def profile_missing_fields(user: User) -> list[str]:
    missing: list[str] = []
    if not (user.full_name or "").strip():
        missing.append("ФИО")
    if not user.birth_date:
        missing.append("дата рождения")
    if not (user.job_title or "").strip():
        missing.append("должность")
    if not (user.business_unit or "").strip():
        missing.append("бизнес-юнит")
    return missing


def is_profile_complete(user: User) -> bool:
    return not profile_missing_fields(user)


def refresh_user(db: Session, user: User) -> User:
    db.refresh(user)
    return user


def require_profile_complete(user: User, *, message: str | None = None) -> None:
    missing = profile_missing_fields(user)
    if not missing:
        return
    fields = ", ".join(missing)
    if message:
        detail = f"{message.rstrip('.')}. Не заполнено: {fields}."
    else:
        detail = f"Заполните в личном кабинете и нажмите «Сохранить»: {fields}."
    raise AppError(detail, status_code=400)
