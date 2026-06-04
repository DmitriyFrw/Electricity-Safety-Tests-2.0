from __future__ import annotations

import datetime as dt
from collections import defaultdict

from sqlalchemy.orm import Session

from app.constants import ATTEMPT_MODE_EXAM, EXAM_TICKET_TIME_LIMIT_SECONDS
from app.models import Attempt, Test, Ticket, TicketAttempt, UserAnswer
from app.repositories import AttemptRepository
from app.services.attempts.scoring import (
    AttemptScore,
    _score_from_test_and_answers,
    build_ticket_result_rows,
)
from app.support.answers import parse_answer_label
from app.support.datetime_utils import ensure_utc_aware, utc_now


def ticket_deadline(started_at: dt.datetime) -> dt.datetime:
    start = ensure_utc_aware(started_at)
    return start + dt.timedelta(seconds=EXAM_TICKET_TIME_LIMIT_SECONDS)


def seconds_remaining(started_at: dt.datetime, *, now: dt.datetime | None = None) -> int:
    when = ensure_utc_aware(now) if now is not None else utc_now()
    left = (ticket_deadline(started_at) - when).total_seconds()
    return max(0, int(left))


def is_ticket_time_expired(ta: TicketAttempt, *, now: dt.datetime | None = None) -> bool:
    if ta.finished_at is not None:
        return bool(ta.timed_out)
    return seconds_remaining(ta.started_at, now=now) <= 0


def get_open_exam_attempt(db: Session, *, user_id: int, test_id: int) -> Attempt | None:
    return AttemptRepository.get_open_exam(db, user_id=user_id, test_id=test_id)


def create_exam_attempt(db: Session, *, user_id: int, test_id: int) -> Attempt:
    existing = get_open_exam_attempt(db, user_id=user_id, test_id=test_id)
    if existing:
        return existing
    attempt = Attempt(
        user_id=user_id,
        test_id=test_id,
        mode=ATTEMPT_MODE_EXAM,
        finished_at=None,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


def _get_ticket_attempt(db: Session, attempt_id: int, ticket_id: int) -> TicketAttempt | None:
    return (
        db.query(TicketAttempt)
        .filter(
            TicketAttempt.attempt_id == attempt_id,
            TicketAttempt.ticket_id == ticket_id,
        )
        .one_or_none()
    )


def _close_other_open_tickets(
    db: Session, attempt: Attempt, test: Test, *, except_ticket_id: int, now: dt.datetime
) -> None:
    open_rows = (
        db.query(TicketAttempt)
        .filter(
            TicketAttempt.attempt_id == attempt.id,
            TicketAttempt.finished_at.is_(None),
            TicketAttempt.ticket_id != except_ticket_id,
        )
        .all()
    )
    tickets_by_id = {t.id: t for t in test.tickets}
    for row in open_rows:
        ticket = tickets_by_id.get(row.ticket_id)
        if not ticket:
            continue
        if is_ticket_time_expired(row, now=now):
            row.timed_out = True
            row.finished_at = now
            _store_empty_ticket_answers(db, attempt, ticket)
        else:
            raise ValueError("Сначала завершите текущий билет")


def start_ticket_for_exam(
    db: Session,
    *,
    attempt: Attempt,
    ticket: Ticket,
    test: Test,
) -> tuple[TicketAttempt, int]:
    now = utc_now()
    _close_other_open_tickets(db, attempt, test, except_ticket_id=ticket.id, now=now)
    ta = _get_ticket_attempt(db, attempt.id, ticket.id)
    if ta and ta.finished_at is not None:
        raise ValueError("Билет уже сдан")

    if ta and ta.finished_at is None:
        if is_ticket_time_expired(ta, now=now):
            ta.timed_out = True
            ta.finished_at = now
            _store_empty_ticket_answers(db, attempt, ticket)
            db.commit()
            raise ValueError("Время на билет истекло")
        return ta, seconds_remaining(ta.started_at, now=now)

    ta = TicketAttempt(attempt_id=attempt.id, ticket_id=ticket.id, started_at=now)
    db.add(ta)
    db.commit()
    db.refresh(ta)
    return ta, EXAM_TICKET_TIME_LIMIT_SECONDS


def _store_empty_ticket_answers(db: Session, attempt: Attempt, ticket: Ticket) -> None:
    for q in ticket.questions:
        existing = (
            db.query(UserAnswer)
            .filter(UserAnswer.attempt_id == attempt.id, UserAnswer.question_id == q.id)
            .one_or_none()
        )
        if not existing:
            db.add(UserAnswer(attempt_id=attempt.id, question_id=q.id, selected_index=None))


def submit_exam_ticket(
    db: Session,
    *,
    attempt: Attempt,
    ticket: Ticket,
    answers: dict[int, str],
) -> None:
    now = utc_now()
    ta = _get_ticket_attempt(db, attempt.id, ticket.id)
    if not ta or ta.finished_at is not None:
        raise ValueError("Сначала начните прохождение билета")
    if is_ticket_time_expired(ta, now=now):
        ta.timed_out = True
        ta.finished_at = now
        _store_empty_ticket_answers(db, attempt, ticket)
        db.commit()
        raise ValueError("Время на билет истекло")

    for q in ticket.questions:
        raw = answers.get(q.id)
        idx = parse_answer_label(str(raw) if raw is not None else "")
        ua = (
            db.query(UserAnswer)
            .filter(UserAnswer.attempt_id == attempt.id, UserAnswer.question_id == q.id)
            .one_or_none()
        )
        if ua:
            ua.selected_index = idx
        else:
            db.add(UserAnswer(attempt_id=attempt.id, question_id=q.id, selected_index=idx))

    ta.finished_at = now
    db.commit()


def completed_ticket_ids(db: Session, attempt: Attempt) -> list[int]:
    rows = (
        db.query(TicketAttempt.ticket_id)
        .filter(TicketAttempt.attempt_id == attempt.id, TicketAttempt.finished_at.isnot(None))
        .all()
    )
    return [r[0] for r in rows]


def next_ticket(test: Test, completed: set[int]) -> Ticket | None:
    for ticket in sorted(test.tickets, key=lambda t: t.position):
        if ticket.id not in completed:
            return ticket
    return None


def finish_exam_attempt(
    db: Session,
    *,
    attempt: Attempt,
    test: Test,
) -> tuple[AttemptScore, list[dict]]:
    if attempt.finished_at is not None:
        raise ValueError("Экзамен уже завершён")

    tickets_sorted = sorted(test.tickets, key=lambda t: t.position)
    for ticket in tickets_sorted:
        ta = _get_ticket_attempt(db, attempt.id, ticket.id)
        if not ta or ta.finished_at is None:
            raise ValueError("Сдайте все билеты перед завершением экзамена")

    attempt.finished_at = utc_now()
    db.commit()
    db.refresh(attempt, attribute_names=["user_answers"])

    t_correct: defaultdict[int, int] = defaultdict(int)
    t_total: defaultdict[int, int] = defaultdict(int)
    by_q = {ua.question_id: ua.selected_index for ua in attempt.user_answers}
    for ticket in tickets_sorted:
        for q in ticket.questions:
            t_total[ticket.id] += 1
            sel = by_q.get(q.id)
            if sel is not None and sel == q.correct_index:
                t_correct[ticket.id] += 1

    summary = _score_from_test_and_answers(test, attempt.user_answers)
    ticket_rows = build_ticket_result_rows(tickets_sorted, t_correct, t_total)
    return summary, ticket_rows
