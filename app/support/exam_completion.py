from __future__ import annotations

from sqlalchemy.orm import Session

from app.constants import ATTEMPT_MODE_EXAM
from app.models import Attempt, TicketAttempt
from app.support.exam_composition import ExamComposition, parse_composition
from app.support.grading import exam_is_passed


def exam_required_ticket_ids(composition: ExamComposition) -> list[int]:
    return [composition.ticket_id]


def exam_all_tickets_completed_normally(
    db: Session,
    attempt: Attempt,
    composition: ExamComposition,
) -> bool:
    """Все билеты экзамена сданы штатно (без таймаута и досрочного закрытия)."""
    for ticket_id in exam_required_ticket_ids(composition):
        ta = (
            db.query(TicketAttempt)
            .filter(
                TicketAttempt.attempt_id == attempt.id,
                TicketAttempt.ticket_id == ticket_id,
            )
            .one_or_none()
        )
        if ta is None or ta.finished_at is None or ta.timed_out:
            return False
    return True


def exam_attempt_is_passed(db: Session, attempt: Attempt, percent: float) -> bool:
    if attempt.mode != ATTEMPT_MODE_EXAM:
        return exam_is_passed(percent)
    composition = parse_composition(attempt.exam_ticket_order)
    if composition is None:
        return False
    if not exam_all_tickets_completed_normally(db, attempt, composition):
        return False
    return exam_is_passed(percent)
