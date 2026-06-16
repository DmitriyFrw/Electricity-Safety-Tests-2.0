from __future__ import annotations

from app.api.mappers import kot_user_out
from app.cache import invalidate_cache
from app.constants import ROLE_KOT
from app.cqrs.messages.staff import (
    ExportExamScheduleQuery,
    ListExamScheduleQuery,
    ListKotUsersQuery,
    UpdateKotSafetyGroupCommand,
)
from app.services.staff.exam_schedule_export import build_exam_schedule_rows, build_exam_schedule_xlsx
from app.repositories import UserRepository
from app.schemas import ExamScheduleRowOut, KotUserOut
from app.support.errors import AppError
from app.support.safety_groups import (
    require_can_manage_safety_groups,
    validate_safety_group_value,
)


class ListKotUsersHandler:
    def handle(self, query: ListKotUsersQuery) -> list[KotUserOut]:
        require_can_manage_safety_groups(query.actor)
        from app.dashboard_stats import display_name

        users = [u for u in UserRepository.list_all(query.db) if u.role == ROLE_KOT]
        users.sort(key=lambda item: display_name(item).casefold())
        return [kot_user_out(u) for u in users]


class ExportExamScheduleHandler:
    def handle(self, query: ExportExamScheduleQuery) -> tuple[bytes, str]:
        require_can_manage_safety_groups(query.actor)
        return build_exam_schedule_xlsx(query.db)


class ListExamScheduleHandler:
    def handle(self, query: ListExamScheduleQuery) -> list[ExamScheduleRowOut]:
        require_can_manage_safety_groups(query.actor)
        return [
            ExamScheduleRowOut(
                full_name=row.full_name,
                birth_date=row.birth_date,
                job_title=row.job_title,
                business_unit=row.business_unit,
                safety_group=row.safety_group,
                role_label=row.role_label,
                last_exam_date=row.last_exam_date,
                next_exam_date=row.next_exam_date,
                exam_grade=row.exam_grade,
            )
            for row in build_exam_schedule_rows(query.db)
        ]


class UpdateKotSafetyGroupHandler:
    def handle(self, command: UpdateKotSafetyGroupCommand) -> KotUserOut:
        require_can_manage_safety_groups(command.actor)
        target = UserRepository.get_by_id(command.db, command.target_user_id)
        if not target:
            raise AppError("Пользователь не найден", status_code=404)
        if target.role != ROLE_KOT:
            raise AppError("Группу по ЭБ можно назначать только пользователям с ролью Кот", status_code=400)

        target.safety_group = validate_safety_group_value(command.form.safety_group)
        command.db.commit()
        command.db.refresh(target)
        invalidate_cache("test_list")
        return kot_user_out(target)
