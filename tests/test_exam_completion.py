from __future__ import annotations

from app.models import Attempt, Question, Ticket, TicketAttempt, Test, UserAnswer
from app.support.exam_completion import exam_attempt_is_passed
from app.support.exam_composition import serialize_composition, ExamComposition


def test_abandoned_exam_not_passed_even_with_high_percent(db_session):
    attempt = Attempt(user_id=1, test_id=1, mode="exam", exam_ticket_order=None)
    db_session.add(attempt)
    db_session.flush()

    composition = ExamComposition(ticket_id=10, question_ids=[101, 102, 103, 104])
    attempt.exam_ticket_order = serialize_composition(composition)
    ta = TicketAttempt(
        attempt_id=attempt.id,
        ticket_id=10,
        timed_out=True,
        finished_at=attempt.started_at,
    )
    db_session.add(ta)
    for qid in composition.question_ids[:3]:
        db_session.add(
            UserAnswer(attempt_id=attempt.id, question_id=qid, selected_index=0)
        )
    db_session.commit()

    assert exam_attempt_is_passed(db_session, attempt, 75.0) is False


def test_normally_finished_exam_can_pass(db_session):
    attempt = Attempt(user_id=1, test_id=1, mode="exam", exam_ticket_order=None)
    db_session.add(attempt)
    db_session.flush()

    composition = ExamComposition(ticket_id=10, question_ids=[101, 102])
    attempt.exam_ticket_order = serialize_composition(composition)
    ta = TicketAttempt(
        attempt_id=attempt.id,
        ticket_id=10,
        timed_out=False,
        finished_at=attempt.started_at,
    )
    db_session.add(ta)
    db_session.commit()

    assert exam_attempt_is_passed(db_session, attempt, 80.0) is True
    assert exam_attempt_is_passed(db_session, attempt, 70.0) is False
