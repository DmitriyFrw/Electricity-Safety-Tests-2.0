from __future__ import annotations

import datetime as dt

from app.services.staff.exam_schedule_export import (
    NOT_TAKEN_EXAM,
    ExamScheduleRow,
    build_exam_schedule_xlsx,
    _format_birth_date,
)


def test_format_birth_date():
    assert _format_birth_date(dt.date(1990, 3, 15)) == "15.03.1990"
    assert _format_birth_date(None) == ""


def test_exam_schedule_row_not_taken():
    row = ExamScheduleRow(
        full_name="Иванов И.И.",
        birth_date="01.01.1990",
        job_title="Инженер",
        business_unit="ДЦ MOZ",
        safety_group="II группа",
        role_label="Кот",
        last_exam_date=NOT_TAKEN_EXAM,
        next_exam_date=NOT_TAKEN_EXAM,
        exam_grade=NOT_TAKEN_EXAM,
    )
    assert row.exam_grade == "не проходил экзамен"
    assert len(row.as_list()) == 9


def test_build_exam_schedule_xlsx_empty_db(db_session):
    payload, filename = build_exam_schedule_xlsx(db_session)
    assert payload[:2] == b"PK"
    assert filename.endswith(".xlsx")


async def test_list_exam_schedule_api(async_client, db_session):
    from app.auth import hash_password
    from app.models import User

    admin = User(username="sched_admin", password_hash=hash_password("password123"), role="admin")
    db_session.add(admin)
    db_session.commit()

    csrf = (await async_client.get("/api/auth/csrf")).json()["csrf_token"]
    login = await async_client.post(
        "/api/auth/login",
        json={"username": "sched_admin", "password": "password123"},
        headers={"X-CSRF-Token": csrf},
    )
    login.raise_for_status()

    response = await async_client.get("/api/staff/exam-schedule")
    response.raise_for_status()
    rows = response.json()
    assert isinstance(rows, list)
    assert len(rows) == 1
    assert rows[0]["full_name"]
    assert rows[0]["exam_grade"] == NOT_TAKEN_EXAM
