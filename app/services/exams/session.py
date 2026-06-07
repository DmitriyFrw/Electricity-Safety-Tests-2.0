from __future__ import annotations

import datetime as dt
from collections import defaultdict

from sqlalchemy.orm import Session

from app.constants import ATTEMPT_MODE_EXAM, EXAM_TICKET_TIME_LIMIT_SECONDS
from app.models import Attempt, Question, Test, Ticket, TicketAttempt, UserAnswer
from app.repositories import AttemptRepository
from app.services.attempts.scoring import (
    AttemptScore,
    build_ticket_result_rows,
    score_exam_questions,
)
from app.support.answers import (
    is_answer_correct,
    question_correct_indices,
    set_user_answer_from_raw,
    user_answer_selected_indices,
)
from app.support.question_options import question_option_count
from app.support.datetime_utils import ensure_utc_aware, utc_now
from app.support.exam_composition import (
    ExamComposition,
    ensure_exam_composition,
    load_exam_questions,
    parse_composition,
)
from app.support.exam_ticket_order import ensure_exam_ticket_order


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


def get_exam_composition(db: Session, attempt: Attempt, test: Test) -> ExamComposition:
    before = attempt.exam_ticket_order
    composition = ensure_exam_ticket_order(db, attempt, test)
    if before != attempt.exam_ticket_order:
        db.commit()
        db.refresh(attempt)
    return composition


def create_exam_attempt(db: Session, *, user_id: int, test_id: int, test: Test) -> Attempt:
    existing = get_open_exam_attempt(db, user_id=user_id, test_id=test_id)
    if existing:
        get_exam_composition(db, existing, test)
        return existing
    attempt = Attempt(
        user_id=user_id,
        test_id=test_id,
        mode=ATTEMPT_MODE_EXAM,
        finished_at=None,
    )
    db.add(attempt)
    db.flush()
    ensure_exam_composition(db, attempt, test.safety_group)
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
    db: Session, attempt: Attempt, *, except_ticket_id: int, now: dt.datetime
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
    for row in open_rows:
        raise ValueError("Сначала завершите текущий билет")


def _store_empty_question_answers(db: Session, attempt: Attempt, question_ids: list[int]) -> None:
    for qid in question_ids:
        existing = (
            db.query(UserAnswer)
            .filter(UserAnswer.attempt_id == attempt.id, UserAnswer.question_id == qid)
            .one_or_none()
        )
        if not existing:
            db.add(UserAnswer(attempt_id=attempt.id, question_id=qid, selected_index=None))


def start_ticket_for_exam(
    db: Session,
    *,
    attempt: Attempt,
    ticket: Ticket,
    composition: ExamComposition,
) -> tuple[TicketAttempt, int]:
    if ticket.id != composition.ticket_id:
        raise ValueError("Билет не найден")
    now = utc_now()
    _close_other_open_tickets(db, attempt, except_ticket_id=ticket.id, now=now)
    ta = _get_ticket_attempt(db, attempt.id, ticket.id)
    if ta and ta.finished_at is not None:
        raise ValueError("Билет уже сдан")

    if ta and ta.finished_at is None:
        if is_ticket_time_expired(ta, now=now):
            ta.timed_out = True
            ta.finished_at = now
            _store_empty_question_answers(db, attempt, composition.question_ids)
            db.commit()
            raise ValueError("Время на билет истекло")
        return ta, seconds_remaining(ta.started_at, now=now)

    ta = TicketAttempt(attempt_id=attempt.id, ticket_id=ticket.id, started_at=now)
    db.add(ta)
    db.commit()
    db.refresh(ta)
    return ta, EXAM_TICKET_TIME_LIMIT_SECONDS


def submit_exam_ticket(
    db: Session,
    *,
    attempt: Attempt,
    ticket: Ticket,
    composition: ExamComposition,
    answers: dict[int, str],
) -> None:
    if ticket.id != composition.ticket_id:
        raise ValueError("Билет не найден")
    now = utc_now()
    ta = _get_ticket_attempt(db, attempt.id, ticket.id)
    if not ta or ta.finished_at is not None:
        raise ValueError("Сначала начните прохождение билета")
    if is_ticket_time_expired(ta, now=now):
        ta.timed_out = True
        ta.finished_at = now
        _store_empty_question_answers(db, attempt, composition.question_ids)
        db.commit()
        raise ValueError("Время на билет истекло")

    questions = load_exam_questions(db, composition.question_ids)
    for q in questions:
        raw = answers.get(q.id)
        ua = (
            db.query(UserAnswer)
            .filter(UserAnswer.attempt_id == attempt.id, UserAnswer.question_id == q.id)
            .one_or_none()
        )
        if not ua:
            ua = UserAnswer(attempt_id=attempt.id, question_id=q.id, selected_index=None)
            db.add(ua)
        set_user_answer_from_raw(
            ua, str(raw) if raw is not None else None, option_count=question_option_count(q)
        )

    ta.finished_at = now
    db.commit()


def completed_ticket_ids(db: Session, attempt: Attempt) -> list[int]:
    rows = (
        db.query(TicketAttempt.ticket_id)
        .filter(TicketAttempt.attempt_id == attempt.id, TicketAttempt.finished_at.isnot(None))
        .all()
    )
    return [r[0] for r in rows]


def next_exam_ticket_id(composition: ExamComposition, completed: set[int]) -> int | None:
    if composition.ticket_id in completed:
        return None
    return composition.ticket_id


def finish_exam_attempt(
    db: Session,
    *,
    attempt: Attempt,
    test: Test,
) -> tuple[AttemptScore, list[dict[str, object]]]:
    if attempt.finished_at is not None:
        raise ValueError("Экзамен уже завершён")

    composition = parse_composition(attempt.exam_ticket_order)
    if not composition:
        raise ValueError("Некорректная экзаменационная сессия")

    ticket = db.get(Ticket, composition.ticket_id)
    if not ticket:
        raise ValueError("Билет экзамена не найден")

    ta = _get_ticket_attempt(db, attempt.id, ticket.id)
    if not ta or ta.finished_at is None:
        raise ValueError("Сдайте билет перед завершением экзамена")

    attempt.finished_at = utc_now()
    db.commit()
    db.refresh(attempt, attribute_names=["user_answers"])

    questions = load_exam_questions(db, composition.question_ids)
    t_correct: defaultdict[int, int] = defaultdict(int)
    t_total: defaultdict[int, int] = defaultdict(int)
    by_q = {ua.question_id: user_answer_selected_indices(ua) for ua in attempt.user_answers}
    t_total[ticket.id] = len(questions)
    for q in questions:
        selected = by_q.get(q.id, [])
        if is_answer_correct(selected, question_correct_indices(q)):
            t_correct[ticket.id] += 1

    summary = score_exam_questions(questions, attempt.user_answers)
    ticket_rows = build_ticket_result_rows([ticket], t_correct, t_total)
    return summary, ticket_rows
