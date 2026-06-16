from __future__ import annotations

import datetime as dt

from app.constants import ATTEMPT_MODE_EXAM
from app.models import Attempt, Test, User
from app.services.pdf.protocol import (
    _attempt_protocol_form_values,
    _profile_form_values,
    build_attempt_protocol_draft_pdf,
    build_protocol_pdf,
)


def _finished_attempt(user_id: int, test_id: int) -> Attempt:
    finished = dt.datetime(2026, 3, 15, 12, 0, tzinfo=dt.timezone.utc)
    return Attempt(
        user_id=user_id,
        test_id=test_id,
        mode=ATTEMPT_MODE_EXAM,
        finished_at=finished,
        started_at=finished,
    )


def test_attempt_protocol_draft_uses_attempt_data_not_profile(db_session):
    author = User(username="author_proto", password_hash="x", role="ezh")
    user = User(
        username="kot_proto",
        password_hash="x",
        role="kot",
        full_name="Иванов Иван",
        birth_date=dt.date(1990, 1, 1),
        job_title="Инженер",
        business_unit="ДЦ MOZ",
        safety_group="II",
    )
    db_session.add(author)
    db_session.flush()
    test = Test(
        author_id=author.id,
        title="Тест ЭБ группа II",
        safety_group="II",
        published=True,
    )
    db_session.add_all([user, test])
    db_session.flush()
    attempt = _finished_attempt(user.id, test.id)
    db_session.add(attempt)
    db_session.commit()

    profile_values = _profile_form_values(db_session, user)
    attempt_values = _attempt_protocol_form_values(db_session, attempt, user, test)

    assert profile_values.protocol_number.endswith(f"{user.id:05d}")
    assert attempt_values.protocol_number == f"2026{attempt.id:05d}"
    assert attempt_values.regulatory_docs == test.title
    assert profile_values.regulatory_docs != test.title
    assert attempt_values.check_date == "15.03.2026"
    assert profile_values.check_reason == "очередная"
    assert attempt_values.check_reason == "по результатам проверки на платформе «Развивайся»"


def test_build_attempt_protocol_draft_returns_pdf(db_session):
    author = User(username="author_pdf", password_hash="x", role="ezh")
    user = User(
        username="kot_pdf",
        password_hash="x",
        role="kot",
        full_name="Петров Пётр",
        birth_date=dt.date(1985, 5, 5),
        job_title="Электромонтер",
        business_unit="ДЦ KLG",
        safety_group="II",
    )
    db_session.add(author)
    db_session.flush()
    test = Test(author_id=author.id, title="Экзамен II", safety_group="II", published=True)
    db_session.add_all([user, test])
    db_session.flush()
    attempt = _finished_attempt(user.id, test.id)
    db_session.add(attempt)
    db_session.commit()

    profile_pdf = build_protocol_pdf(db_session, user)
    attempt_pdf = build_attempt_protocol_draft_pdf(db_session, attempt, user, test)

    assert profile_pdf[:4] == b"%PDF"
    assert attempt_pdf[:4] == b"%PDF"
    assert profile_pdf != attempt_pdf
