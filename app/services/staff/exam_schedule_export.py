from __future__ import annotations

import datetime as dt
import io
from dataclasses import dataclass

from openpyxl import Workbook
from openpyxl.styles import Font
from sqlalchemy.orm import Session

from app.constants import ATTEMPT_MODE_EXAM, KNOWLEDGE_CHECK_INTERVAL_DAYS, ROLE_KOT
from app.dashboard_stats import display_name
from app.models import Attempt, User
from app.repositories import UserRepository
from app.repositories.options import ATTEMPT_DASHBOARD_OPTIONS
from app.roles import role_label
from app.services.attempts.scoring import score_attempt
from app.support.exam_completion import exam_attempt_is_passed
from app.support.exam_history import format_protocol_date
from app.support.grading import grade_for_exam_protocol
from app.support.safety_groups import effective_safety_group, safety_group_label

NOT_TAKEN_EXAM = "не проходил экзамен"

HEADERS = (
    "ФИО",
    "Дата рождения",
    "Должность",
    "Бизнес-юнит",
    "Группа по ЭБ",
    "Роль",
    "Последняя дата сдачи экзамена",
    "Планируемая дата сдачи экзамена",
    "Оценка за экзамен",
)


@dataclass(frozen=True)
class ExamScheduleRow:
    full_name: str
    birth_date: str
    job_title: str
    business_unit: str
    safety_group: str
    role_label: str
    last_exam_date: str
    next_exam_date: str
    exam_grade: str

    def as_list(self) -> list[str]:
        return [
            self.full_name,
            self.birth_date,
            self.job_title,
            self.business_unit,
            self.safety_group,
            self.role_label,
            self.last_exam_date,
            self.next_exam_date,
            self.exam_grade,
        ]


def _format_birth_date(value: dt.date | None) -> str:
    if value is None:
        return ""
    return value.strftime("%d.%m.%Y")


def _safety_group_for_user(user: User) -> str:
    if user.role == ROLE_KOT:
        return safety_group_label(effective_safety_group(user))
    if user.safety_group:
        return safety_group_label(user.safety_group)
    return ""


def _profile_full_name(user: User) -> str:
    if user.full_name and user.full_name.strip():
        return user.full_name.strip()
    return display_name(user)


def _index_passed_exams(db: Session) -> dict[int, tuple[dt.datetime, str]]:
    attempts = (
        db.query(Attempt)
        .options(*ATTEMPT_DASHBOARD_OPTIONS)
        .filter(
            Attempt.mode == ATTEMPT_MODE_EXAM,
            Attempt.finished_at.isnot(None),
        )
        .order_by(Attempt.finished_at.desc())
        .all()
    )
    passed: dict[int, tuple[dt.datetime, str]] = {}
    for attempt in attempts:
        if attempt.user_id in passed:
            continue
        finished = attempt.finished_at
        if finished is None:
            continue
        summary = score_attempt(db, attempt)
        if not exam_attempt_is_passed(db, attempt, summary.percent):
            continue
        passed[attempt.user_id] = (finished, grade_for_exam_protocol(summary.percent))
    return passed


def build_exam_schedule_rows(db: Session) -> list[ExamScheduleRow]:
    passed_by_user = _index_passed_exams(db)
    users = UserRepository.list_all(db)
    users.sort(key=lambda user: _profile_full_name(user).casefold())

    rows: list[ExamScheduleRow] = []
    for user in users:
        passed = passed_by_user.get(user.id)
        if passed is None:
            rows.append(
                ExamScheduleRow(
                    full_name=_profile_full_name(user),
                    birth_date=_format_birth_date(user.birth_date),
                    job_title=(user.job_title or "").strip(),
                    business_unit=(user.business_unit or "").strip(),
                    safety_group=_safety_group_for_user(user),
                    role_label=role_label(user.role),
                    last_exam_date=NOT_TAKEN_EXAM,
                    next_exam_date=NOT_TAKEN_EXAM,
                    exam_grade=NOT_TAKEN_EXAM,
                )
            )
            continue

        finished_at, grade = passed
        next_date = finished_at.date() + dt.timedelta(days=KNOWLEDGE_CHECK_INTERVAL_DAYS)
        rows.append(
            ExamScheduleRow(
                full_name=_profile_full_name(user),
                birth_date=_format_birth_date(user.birth_date),
                job_title=(user.job_title or "").strip(),
                business_unit=(user.business_unit or "").strip(),
                safety_group=_safety_group_for_user(user),
                role_label=role_label(user.role),
                last_exam_date=format_protocol_date(finished_at),
                next_exam_date=next_date.strftime("%d.%m.%Y"),
                exam_grade=grade,
            )
        )
    return rows


def build_exam_schedule_xlsx(db: Session) -> tuple[bytes, str]:
    rows = build_exam_schedule_rows(db)
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "График экзаменов"

    worksheet.append(list(HEADERS))
    for cell in worksheet[1]:
        cell.font = Font(bold=True)

    for row in rows:
        worksheet.append(row.as_list())

    for column in worksheet.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            value = str(cell.value or "")
            max_length = max(max_length, len(value))
        worksheet.column_dimensions[column_letter].width = min(max(max_length + 2, 12), 48)

    buffer = io.BytesIO()
    workbook.save(buffer)
    today = dt.date.today().strftime("%Y-%m-%d")
    return buffer.getvalue(), f"grafik_ebkamena_{today}.xlsx"
