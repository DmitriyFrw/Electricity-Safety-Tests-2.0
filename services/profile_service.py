from __future__ import annotations

from sqlalchemy.orm import Session

from app.api.mappers import user_out
from app.dto import ExportRequestDTO
from app.form_requests.profile import ProfileUpdateRequest
from app.models import User
from app.policies import AccessPolicy
from app.schemas import UserOut
from app.services.exports import ExportService
from app.services.pdf.protocol import build_protocol_pdf
from app.support.errors import AppError
from app.support.profile import require_profile_complete


class ProfileService:
    @staticmethod
    def get_profile(user: User) -> UserOut:
        return user_out(user)

    @staticmethod
    def update_profile(db: Session, user: User, form: ProfileUpdateRequest) -> UserOut:
        if not AccessPolicy.can_manage_profile_pdf(user):
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
        if not AccessPolicy.can_manage_profile_pdf(user):
            raise AppError(
                "Формирование протокола доступно только роли Кот",
                status_code=403,
            )
        require_profile_complete(
            user,
            message="Заполните ФИО, дату рождения и должность в личном кабинете",
        )
        return build_protocol_pdf(user)

    @staticmethod
    def build_protocol_pdf_async(user: User) -> str:
        if not AccessPolicy.can_manage_profile_pdf(user):
            raise AppError("Формирование протокола доступно только роли Кот", status_code=403)
        require_profile_complete(
            user,
            message="Заполните ФИО, дату рождения и должность в личном кабинете",
        )
        return ExportService.create_protocol_export(user)

    @staticmethod
    def export_attempts_async(user: User, test_id: int | None = None) -> str:
        req = ExportRequestDTO(user_id=user.id, test_id=test_id, kind="exam_results")
        return ExportService.create_exam_results_export(req)
