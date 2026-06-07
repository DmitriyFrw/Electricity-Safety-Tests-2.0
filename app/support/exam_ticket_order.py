from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Attempt, Test
from app.support.exam_composition import ExamComposition, ensure_exam_composition


def ensure_exam_ticket_order(db: Session, attempt: Attempt, test: Test) -> ExamComposition:
    """Совместимое имя: экзамен = один билет с вопросами из группы ЭБ."""
    return ensure_exam_composition(db, attempt, test.safety_group)


def ticket_index_in_order(_order: ExamComposition | list[int], ticket_id: int) -> int:
    if isinstance(_order, ExamComposition):
        return 1 if _order.ticket_id == ticket_id else 0
    return _order.index(ticket_id) + 1 if ticket_id in _order else 0
