from __future__ import annotations

import datetime as dt
from typing import Any, Optional

from sqlalchemy.orm import Session, selectinload

from app.attempt_service import score_attempt
from app.constants import (
    DEFAULT_SAFETY_GROUP,
    DEFAULT_SAFETY_GROUP_DESC,
    KNOWLEDGE_CHECK_INTERVAL_DAYS,
    MAX_ERRORS_DISPLAY,
    MIN_PASS_PERCENT,
)
from app.models import Attempt, Test, User
from app.validation import test_is_ready_to_take


def display_name(user: User) -> str:
    name = (user.username or "").strip()
    if not name:
        return "Пользователь"
    if " " in name:
        return name
    if len(name) <= 3:
        return name.upper()
    return name[0].upper() + name[1:]


def build_dashboard_context(db: Session, user: User) -> dict[str, Any]:
    tests = (
        db.query(Test)
        .options(selectinload(Test.tickets))
        .order_by(Test.created_at.desc())
        .all()
    )

    tickets_count = 0
    exam_test_id: Optional[int] = None
    materials_updated: Optional[dt.datetime] = None

    for t in tests:
        if materials_updated is None or t.created_at > materials_updated:
            materials_updated = t.created_at
        if test_is_ready_to_take(db, t):
            tickets_count += len(t.tickets)
            if exam_test_id is None:
                exam_test_id = t.id

    attempts = (
        db.query(Attempt)
        .options(selectinload(Attempt.test), selectinload(Attempt.user_answers))
        .filter(Attempt.user_id == user.id, Attempt.finished_at.isnot(None))
        .order_by(Attempt.finished_at.desc())
        .limit(50)
        .all()
    )

    last_percent: Optional[float] = None
    last_errors: Optional[int] = None
    last_grade: Optional[str] = None
    last_grade_class: Optional[str] = None
    last_test_title: Optional[str] = None
    last_test_date: Optional[dt.datetime] = None
    next_check_date: Optional[dt.date] = None

    if attempts:
        last = attempts[0]
        s = score_attempt(db, last)
        last_percent = s.percent
        last_errors = s.errors
        last_grade = s.grade
        last_grade_class = s.grade_class
        last_test_title = last.test.title if last.test else None
        last_test_date = last.finished_at
        if last.finished_at:
            next_check_date = last.finished_at.date() + dt.timedelta(
                days=KNOWLEDGE_CHECK_INTERVAL_DAYS
            )

    if next_check_date is None:
        next_check_date = dt.date.today() + dt.timedelta(days=90)

    dn = display_name(user)
    return {
        "user_display": dn,
        "display_name": dn,
        "safety_group": DEFAULT_SAFETY_GROUP,
        "safety_group_desc": DEFAULT_SAFETY_GROUP_DESC,
        "tickets_count": tickets_count,
        "exam_test_id": exam_test_id,
        "exam_href": f"/tests/{exam_test_id}/take" if exam_test_id else "/tests/catalog",
        "min_pass_percent": MIN_PASS_PERCENT,
        "max_errors_allowed": MAX_ERRORS_DISPLAY,
        "materials_updated": materials_updated,
        "last_percent": last_percent,
        "last_errors": last_errors,
        "last_grade": last_grade,
        "last_grade_class": last_grade_class,
        "last_test_title": last_test_title,
        "last_test_date": last_test_date,
        "next_check_date": next_check_date,
        "created_tests_count": db.query(Test).filter(Test.author_id == user.id).count(),
        "has_attempts": bool(attempts),
    }
