from __future__ import annotations

from app.api.mappers import user_out
from app.cqrs.messages.profile import (
    BuildProtocolPdfQuery,
    GetProfileQuery,
    StartAttemptsExportCommand,
    StartProtocolExportCommand,
    UpdateProfileCommand,
)
from app.dto import ExportRequestDTO
from app.policies import AccessPolicy
from app.schemas import UserOut
from app.services.exports.export_service import ExportService
from app.services.pdf.protocol import build_protocol_pdf
from app.support.errors import AppError
from app.support.profile import refresh_user, require_profile_complete


class GetProfileHandler:
    def handle(self, query: GetProfileQuery) -> UserOut:
        return user_out(query.user)


class UpdateProfileHandler:
    def handle(self, command: UpdateProfileCommand) -> UserOut:
        if not AccessPolicy.can_manage_profile_pdf(command.user):
            raise AppError(
                "Редактирование профиля для PDF доступно только роли Кот",
                status_code=403,
            )
        command.user.full_name = command.form.full_name
        command.user.birth_date = command.form.birth_date
        command.user.job_title = command.form.job_title
        command.user.business_unit = command.form.business_unit
        command.db.commit()
        command.db.refresh(command.user)
        return user_out(command.user)


class BuildProtocolPdfHandler:
    def handle(self, query: BuildProtocolPdfQuery) -> bytes:
        if not AccessPolicy.can_manage_profile_pdf(query.user):
            raise AppError(
                "Формирование протокола доступно только роли Кот",
                status_code=403,
            )
        user = refresh_user(query.db, query.user)
        require_profile_complete(user)
        return build_protocol_pdf(query.db, user)


class StartProtocolExportHandler:
    def handle(self, command: StartProtocolExportCommand) -> str:
        if not AccessPolicy.can_manage_profile_pdf(command.user):
            raise AppError("Формирование протокола доступно только роли Кот", status_code=403)
        user = refresh_user(command.db, command.user)
        require_profile_complete(user)
        return ExportService.create_protocol_export(user.id)


class StartAttemptsExportHandler:
    def handle(self, command: StartAttemptsExportCommand) -> str:
        req = ExportRequestDTO.model_validate(
            {
                "user_id": command.user.id,
                "test_id": command.test_id,
                "kind": "exam_results",
            }
        )
        return ExportService.create_exam_results_export(req)
