from __future__ import annotations

import json
import random

from sqlalchemy.orm import Session

from app.models import Attempt, Test, Ticket
from app.support.exam_composition import ExamComposition, ensure_exam_composition
from app.support.validation import complete_tickets_sorted


def serialize_ticket_id_order(ticket_ids: list[int]) -> str:
    return json.dumps(ticket_ids)


def parse_ticket_id_order(raw: str | None) -> list[int] | None:
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, list) or not data:
        return None
    if not all(isinstance(x, int) for x in data):
        return None
    return data


def tickets_by_id_order(test: Test, ticket_ids: list[int]) -> list[Ticket]:
    by_id = {ticket.id: ticket for ticket in complete_tickets_sorted(test)}
    return [by_id[ticket_id] for ticket_id in ticket_ids if ticket_id in by_id]


def pick_exam_source_ticket(test: Test, *, group_tickets: list[Ticket]) -> Ticket:
    """Билет-носитель экзамена: из билетов текущего теста с учётом random_ticket_order."""
    own = complete_tickets_sorted(test)
    candidates = own or group_tickets
    if not candidates:
        raise ValueError("Нет готовых билетов для экзамена")
    if test.random_ticket_order:
        return random.choice(candidates)
    return sorted(candidates, key=lambda ticket: ticket.position)[0]


def ensure_exam_ticket_order(db: Session, attempt: Attempt, test: Test) -> ExamComposition:
    return ensure_exam_composition(db, attempt, test)


def ensure_training_ticket_order(db: Session, attempt: Attempt, test: Test) -> list[int]:
    """Порядок билетов в тренировке: по position или перемешанный (фиксируется в попытке)."""
    sorted_ids = [ticket.id for ticket in complete_tickets_sorted(test)]
    if not sorted_ids:
        return []

    if not test.random_ticket_order:
        if parse_ticket_id_order(attempt.exam_ticket_order) is not None:
            attempt.exam_ticket_order = None
            db.commit()
        return sorted_ids

    existing = parse_ticket_id_order(attempt.exam_ticket_order)
    if existing is not None and set(existing) == set(sorted_ids):
        return existing

    shuffled = list(sorted_ids)
    random.shuffle(shuffled)
    attempt.exam_ticket_order = serialize_ticket_id_order(shuffled)
    db.commit()
    return shuffled


def ticket_index_in_order(_order: ExamComposition | list[int], ticket_id: int) -> int:
    if isinstance(_order, ExamComposition):
        return 1 if _order.ticket_id == ticket_id else 0
    return _order.index(ticket_id) + 1 if ticket_id in _order else 0
