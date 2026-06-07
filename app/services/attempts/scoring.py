from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Mapping

import datetime as dt

from sqlalchemy.orm import Session

from app.constants import ATTEMPT_MODE_EXAM, ATTEMPT_MODE_TRAINING
from app.models import Attempt, Question, Test, Ticket, UserAnswer
from app.repositories import TestRepository
from app.support.exam_composition import load_exam_questions, parse_composition
from app.support.validation import complete_tickets_sorted
from app.support.question_options import question_option_count
from app.support.answers import (
    is_answer_correct,
    parse_answer_labels,
    question_correct_indices,
    set_user_answer_from_raw,
    user_answer_selected_indices,
)
from app.support.grading import grade_css_class, grade_for_percent, score_percent


@dataclass(frozen=True)
class AttemptScore:
    correct: int
    total: int
    percent: float
    errors: int
    grade: str
    grade_class: str


def _answers_by_question(user_answers: list[UserAnswer]) -> dict[int, list[int]]:
    return {ua.question_id: user_answer_selected_indices(ua) for ua in user_answers}


def attempted_tickets(test: Test, answered_question_ids: set[int]) -> list[Ticket]:
    """Билеты, в которых есть хотя бы один ответ (досрочное завершение — только они в оценке)."""
    if not answered_question_ids:
        return []
    attempted: list[Ticket] = []
    for ticket in complete_tickets_sorted(test):
        if any(q.id in answered_question_ids for q in ticket.questions):
            attempted.append(ticket)
    return attempted


def score_attempt(db: Session, attempt: Attempt) -> AttemptScore:
    if not attempt.user_answers:
        db.refresh(attempt, attribute_names=["user_answers"])
    if attempt.mode == ATTEMPT_MODE_EXAM:
        composition = parse_composition(attempt.exam_ticket_order)
        if composition:
            questions = load_exam_questions(db, composition.question_ids)
            return score_exam_questions(questions, attempt.user_answers)
    test = TestRepository.get_full(db, attempt.test_id)
    if not test:
        raise ValueError("Test not found")
    return _score_from_test_and_answers(test, attempt.user_answers)


def _score_from_test_and_answers(test: Test, user_answers: list[UserAnswer]) -> AttemptScore:
    by_q = _answers_by_question(user_answers)
    tickets = attempted_tickets(test, set(by_q.keys()))
    correct = 0
    total = 0
    for ticket in tickets:
        for q in ticket.questions:
            total += 1
            selected = by_q.get(q.id, [])
            if is_answer_correct(selected, question_correct_indices(q)):
                correct += 1
    if total == 0:
        return AttemptScore(
            correct=0,
            total=0,
            percent=0.0,
            errors=0,
            grade=grade_for_percent(0),
            grade_class=grade_css_class(0),
        )
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


def score_exam_questions(questions: list[Question], user_answers: list[UserAnswer]) -> AttemptScore:
    by_q = _answers_by_question(user_answers)
    correct = 0
    total = len(questions)
    for q in questions:
        selected = by_q.get(q.id, [])
        if is_answer_correct(selected, question_correct_indices(q)):
            correct += 1
    if total == 0:
        return AttemptScore(
            correct=0,
            total=0,
            percent=0.0,
            errors=0,
            grade=grade_for_percent(0),
            grade_class=grade_css_class(0),
        )
    pct = score_percent(correct, total)
    return AttemptScore(
        correct=correct,
        total=total,
        percent=round(pct, 1),
        errors=total - correct,
        grade=grade_for_percent(pct),
        grade_class=grade_css_class(pct),
    )


def _question_result_payload(
    *,
    q: Question,
    ticket: Ticket,
    ticket_position: int,
    ticket_title: str | None,
    question_position: int,
    user_answers: list[UserAnswer],
) -> dict[str, Any]:
    by_q = _answers_by_question(user_answers)
    selected = by_q.get(q.id, [])
    correct_indices = question_correct_indices(q)
    correct_idx = correct_indices[0]
    selected_index = selected[0] if len(selected) == 1 else None
    return {
        "question_id": q.id,
        "ticket_id": ticket.id,
        "ticket_position": ticket_position,
        "ticket_title": ticket_title,
        "question_position": question_position,
        "question_text": q.text,
        "option_a": q.option_a,
        "option_b": q.option_b,
        "option_c": q.option_c,
        "option_d": q.option_d,
        "option_count": question_option_count(q),
        "correct_index": correct_idx,
        "correct_indexes": correct_indices,
        "selected_index": selected_index,
        "selected_indexes": selected,
        "is_correct": is_answer_correct(selected, correct_indices),
    }


def build_exam_question_result_rows(
    source_ticket: Ticket,
    questions: list[Question],
    user_answers: list[UserAnswer],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pos, q in enumerate(questions, start=1):
        ticket = q.ticket if q.ticket else source_ticket
        payload = _question_result_payload(
            q=q,
            ticket=ticket,
            ticket_position=1,
            ticket_title=source_ticket.title,
            question_position=pos,
            user_answers=user_answers,
        )
        rows.append(payload)
    return rows


def build_question_result_rows(
    test: Test,
    user_answers: list[UserAnswer],
) -> list[dict[str, Any]]:
    by_q = _answers_by_question(user_answers)
    rows: list[dict[str, Any]] = []
    for ticket in attempted_tickets(test, set(by_q.keys())):
        for q in sorted(ticket.questions, key=lambda x: x.position):
            rows.append(
                _question_result_payload(
                    q=q,
                    ticket=ticket,
                    ticket_position=ticket.position,
                    ticket_title=ticket.title,
                    question_position=q.position,
                    user_answers=user_answers,
                )
            )
    return rows


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
    finished_at: dt.datetime | None = None,
) -> tuple[Attempt, AttemptScore, list[dict[str, Any]]]:
    when = finished_at or dt.datetime.now(dt.timezone.utc)
    attempt = Attempt(
        user_id=user_id,
        test_id=test.id,
        mode=ATTEMPT_MODE_TRAINING,
        finished_at=when,
    )
    db.add(attempt)
    db.flush()

    answered_ids = {qid for qid, raw in answers.items() if raw and str(raw).strip()}
    tickets_sorted = attempted_tickets(test, answered_ids)
    if not tickets_sorted:
        raise ValueError("Нет ответов для оценки")

    t_correct: defaultdict[int, int] = defaultdict(int)
    t_total: defaultdict[int, int] = defaultdict(int)
    stored: list[UserAnswer] = []

    for ticket in tickets_sorted:
        for q in ticket.questions:
            t_total[ticket.id] += 1
            raw = answers.get(q.id)
            ua = UserAnswer(attempt_id=attempt.id, question_id=q.id, selected_index=None)
            selected = set_user_answer_from_raw(
                ua, str(raw) if raw is not None else None, option_count=question_option_count(q)
            )
            db.add(ua)
            stored.append(ua)
            if is_answer_correct(selected, question_correct_indices(q)):
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
    finished_at: dt.datetime | None = None,
) -> tuple[Attempt, AttemptScore, list[dict[str, Any]]]:
    answers: dict[int, str] = {}
    for ticket in complete_tickets_sorted(test):
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
