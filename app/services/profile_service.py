from __future__ import annotations

from sqlalchemy.orm import Session

from app.api_serializers import user_out
from app.constants import ROLE_KOT
from app.exceptions import AppError
from app.form_requests.profile import ProfileUpdateRequest
from app.models import User
from app.pdf_service import build_protocol_pdf
from app.schemas import UserOut


class ProfileService:
    @staticmethod
    def get_profile(user: User) -> UserOut:
        return user_out(user)

    @staticmethod
    def update_profile(db: Session, user: User, form: ProfileUpdateRequest) -> UserOut:
        if user.role != ROLE_KOT:
            raise AppError(
                "Редактирование профиля для PDF доступно только роли Кот",
                status_code=403,
            )
        user.full_name = form.full_name
        user.birth_date = form.birth_date
        user.job_title = form.job_title
        db.commit()
        db.refresh(user)
        return user_out(user)

    @staticmethod
    def build_protocol_pdf(user: User) -> bytes:
        if user.role != ROLE_KOT:
            raise AppError(
                "Формирование протокола доступно только роли Кот",
                status_code=403,
            )
        if not user.full_name or not user.birth_date or not user.job_title:
            raise AppError(
                "Заполните ФИО, дату рождения и должность в личном кабинете",
                status_code=400,
            )
        return build_protocol_pdf(user)
