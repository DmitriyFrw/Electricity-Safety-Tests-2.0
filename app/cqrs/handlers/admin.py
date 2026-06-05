from __future__ import annotations

from app.api.mappers import user_admin_out
from app.cqrs.messages.admin import (
    GetUserProtocolDraftPdfQuery,
    ListUsersQuery,
    UpdateUserRoleCommand,
)
from app.policies import AccessPolicy
from app.repositories import UserRepository
from app.schemas import UserAdminOut
from app.services.pdf.protocol import build_protocol_pdf
from app.support.errors import AppError
from app.support.profile import require_profile_complete


class ListUsersHandler:
    def handle(self, query: ListUsersQuery) -> list[UserAdminOut]:
        users = UserRepository.list_all(query.db)
        return [user_admin_out(u) for u in users]


class UpdateUserRoleHandler:
    def handle(self, command: UpdateUserRoleCommand) -> UserAdminOut:
        if not AccessPolicy.can_manage_users(command.actor):
            raise AppError("Управление пользователями доступно только администратору", status_code=403)

        if command.actor.id == command.target_user_id:
            raise AppError("Нельзя изменить свою собственную роль", status_code=400)

        target = UserRepository.get_by_id(command.db, command.target_user_id)
        if not target:
            raise AppError("Пользователь не найден", status_code=404)

        target.role = command.form.role
        command.db.commit()
        command.db.refresh(target)
        return user_admin_out(target)


class GetUserProtocolDraftPdfHandler:
    def handle(self, query: GetUserProtocolDraftPdfQuery) -> bytes:
        if not AccessPolicy.can_export_user_protocol_draft(query.actor):
            raise AppError(
                "Выгрузка черновика протокола доступна только администратору",
                status_code=403,
            )
        target = UserRepository.get_by_id(query.db, query.target_user_id)
        if not target:
            raise AppError("Пользователь не найден", status_code=404)
        require_profile_complete(target)
        return build_protocol_pdf(query.db, target)
