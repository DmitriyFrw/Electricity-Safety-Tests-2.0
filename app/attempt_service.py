from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Mapping, Optional

import datetime as dt

from sqlalchemy.orm import Session, selectinload

from app.answer_labels import parse_answer_label
from app.grading import grade_css_class, grade_for_percent, score_percent
from app.models import Attempt, Question, Test, Ticket, UserAnswer


@dataclass(frozen=True)
class AttemptScore:
    correct: int
    total: int
    percent: float
    errors: int
    grade: str
    grade_class: str


def _load_test_with_questions(db: Session, test_id: int) -> Test:
    return (
        db.query(Test)
        .options(selectinload(Test.tickets).selectinload(Ticket.questions))
        .filter(Test.id == test_id)
        .one()
    )


def score_attempt(db: Session, attempt: Attempt) -> AttemptScore:
    """Подсчёт правильных ответов по сохранённой попытке."""
    if not attempt.user_answers:
        db.refresh(attempt, attribute_names=["user_answers"])
    test = _load_test_with_questions(db, attempt.test_id)
    return _score_from_test_and_answers(test, attempt.user_answers)


def _score_from_test_and_answers(test: Test, user_answers: list[UserAnswer]) -> AttemptScore:
    by_q = {ua.question_id: ua.selected_index for ua in user_answers}
    correct = 0
    total = 0
    for ticket in test.tickets:
        for q in ticket.questions:
            total += 1
            sel = by_q.get(q.id)
            if sel is not None and sel == q.correct_index:
                correct += 1
    pct = score_percent(correct, total)
    return AttemptScore(
        correct=correct,
        total=total,
        percent=round(pct, 1),
        errors=total - correct,
        grade=grade_for_percent(pct),
        grade_class=grade_css_class(pct),
    )


def attempt_to_row(db: Session, attempt: Attempt) -> dict[str, Any]:
    s = score_attempt(db, attempt)
    return {
        "attempt": attempt,
        "test": attempt.test,
        "correct": s.correct,
        "total": s.total,
        "percent": s.percent,
        "errors": s.errors,
        "grade": s.grade,
        "grade_class": s.grade_class,
    }


def build_ticket_result_rows(
    tickets_sorted: list[Ticket],
    t_correct: Mapping[int, int],
    t_total: Mapping[int, int],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for n, ticket in enumerate(tickets_sorted, start=1):
        tc = t_correct[ticket.id]
        tt = t_total[ticket.id]
        pct = score_percent(tc, tt)
        rows.append(
            {
                "n": n,
                "correct": tc,
                "total": tt,
                "percent": round(pct, 1),
                "grade": grade_for_percent(pct),
                "grade_class": grade_css_class(pct),
            }
        )
    return rows


def submit_test_attempt_with_answers(
    db: Session,
    *,
    user_id: int,
    test: Test,
    answers: Mapping[int, str],
    finished_at: Optional[dt.datetime] = None,
) -> tuple[Attempt, AttemptScore, list[dict[str, Any]]]:
    """Сохраняет попытку: answers — словарь question_id -> A|B|C|D|1|2|3|4."""
    when = finished_at or dt.datetime.now(dt.timezone.utc)
    attempt = Attempt(user_id=user_id, test_id=test.id, finished_at=when)
    db.add(attempt)
    db.flush()

    tickets_sorted = sorted(test.tickets, key=lambda t: t.position)
    t_correct: defaultdict[int, int] = defaultdict(int)
    t_total: defaultdict[int, int] = defaultdict(int)
    stored: list[UserAnswer] = []

    for ticket in tickets_sorted:
        for q in ticket.questions:
            t_total[ticket.id] += 1
            raw = answers.get(q.id)
            idx = parse_answer_label(str(raw) if raw is not None else "")
            ua = UserAnswer(attempt_id=attempt.id, question_id=q.id, selected_index=idx)
            db.add(ua)
            stored.append(ua)
            if idx is not None and idx == q.correct_index:
                t_correct[ticket.id] += 1

    db.commit()
    db.refresh(attempt)

    summary = _score_from_test_and_answers(test, stored)
    ticket_rows = build_ticket_result_rows(tickets_sorted, t_correct, t_total)
    return attempt, summary, ticket_rows


def submit_test_attempt(
    db: Session,
    *,
    user_id: int,
    test: Test,
    form: Mapping[str, Any],
    finished_at: Optional[dt.datetime] = None,
) -> tuple[Attempt, AttemptScore, list[dict[str, Any]]]:
    """Совместимость с HTML-формами: поля q_{question_id}."""
    answers: dict[int, str] = {}
    for ticket in test.tickets:
        for q in ticket.questions:
            raw = form.get(f"q_{q.id}")
            if raw is not None:
                answers[q.id] = str(raw)
    return submit_test_attempt_with_answers(
        db,
        user_id=user_id,
        test=test,
        answers=answers,
        finished_at=finished_at,
    )
