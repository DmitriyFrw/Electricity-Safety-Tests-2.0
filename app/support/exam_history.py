from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.constants import ATTEMPT_MODE_EXAM
from app.models import Attempt
from app.repositories.options import ATTEMPT_DASHBOARD_OPTIONS
from app.services.attempts.scoring import score_attempt
from app.support.grading import exam_is_passed, grade_for_exam_protocol


@dataclass(frozen=True)
class PassedExamResult:
    attempt_id: int
    test_id: int
    finished_at: dt.datetime
    percent: float
    grade: str


def format_protocol_date(value: dt.datetime | dt.date | None) -> str:
    if value is None:
        return ""
    if isinstance(value, dt.datetime):
        value = value.astimezone(dt.timezone.utc).date()
    return value.strftime("%d.%m.%Y")


def _iter_passed_exam_attempts(
    db: Session,
    user_id: int,
    *,
    exclude_attempt_id: int | None = None,
) -> list[tuple[Attempt, float]]:
    attempts = (
        db.query(Attempt)
        .options(*ATTEMPT_DASHBOARD_OPTIONS)
        .filter(
            Attempt.user_id == user_id,
            Attempt.mode == ATTEMPT_MODE_EXAM,
            Attempt.finished_at.isnot(None),
        )
        .order_by(Attempt.finished_at.desc())
        .all()
    )
    passed: list[tuple[Attempt, float]] = []
    for attempt in attempts:
        if exclude_attempt_id is not None and attempt.id == exclude_attempt_id:
            continue
        summary = score_attempt(db, attempt)
        if exam_is_passed(summary.percent):
            passed.append((attempt, summary.percent))
    return passed


def last_passed_exam_result(
    db: Session,
    user_id: int,
    *,
    exclude_attempt_id: int | None = None,
) -> PassedExamResult | None:
    """Последняя успешная экзаменационная попытка (удовлетворительно и выше)."""
    rows = _iter_passed_exam_attempts(db, user_id, exclude_attempt_id=exclude_attempt_id)
    if not rows:
        return None
    attempt, percent = rows[0]
    finished = attempt.finished_at
    if finished is None:
        return None
    pct = float(percent)
    return PassedExamResult(
        attempt_id=attempt.id,
        test_id=attempt.test_id,
        finished_at=finished,
        percent=pct,
        grade=grade_for_exam_protocol(pct),
    )


def last_passed_exam_finished_at(
    db: Session,
    user_id: int,
    *,
    exclude_attempt_id: int | None = None,
) -> dt.datetime | None:
    result = last_passed_exam_result(db, user_id, exclude_attempt_id=exclude_attempt_id)
    return result.finished_at if result else None


def format_exam_result_line(*, grade: str, percent: float | None = None) -> str:
    """Текст оценки для строки протокола (удовлетворительно / хорошо / отлично)."""
    return grade
