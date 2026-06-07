from __future__ import annotations

from sqlalchemy.orm import Session, selectinload

from app.constants import MAX_TICKETS_PER_TEST, QUESTIONS_PER_TICKET
from app.models import Test, Ticket
from app.support.answers import question_correct_indices
from app.support.question_options import (
    clamp_correct_index,
    question_option_count,
    question_option_values,
)
from app.support.rich_text import plain_text_from_rich

_EXPECTED_POSITIONS = frozenset(range(1, QUESTIONS_PER_TICKET + 1))


def ticket_is_complete(ticket: Ticket) -> bool:
    qs = sorted(ticket.questions, key=lambda q: q.position)
    if len(qs) != QUESTIONS_PER_TICKET:
        return False
    positions = {q.position for q in qs}
    if positions != _EXPECTED_POSITIONS:
        return False
    for q in qs:
        n = question_option_count(q)
        indices = question_correct_indices(q)
        if not indices:
            return False
        if any(i < 0 or i >= n or i != clamp_correct_index(i, n) for i in indices):
            return False
        if not plain_text_from_rich(q.text or ""):
            return False
        for opt in question_option_values(q, n):
            if not plain_text_from_rich(opt or ""):
                return False
    return True


def complete_tickets(test: Test) -> list[Ticket]:
    return [ticket for ticket in test.tickets if ticket_is_complete(ticket)]


def complete_tickets_sorted(test: Test) -> list[Ticket]:
    return sorted(complete_tickets(test), key=lambda t: t.position)


def test_is_ready_loaded(test: Test) -> bool:
    """Все билеты теста полностью заполнены."""
    if not test.tickets:
        return False
    return all(ticket_is_complete(ticket) for ticket in test.tickets)


def test_is_ready_to_take(db: Session, test: Test) -> bool:
    """Хотя бы один билет с 10 вопросами — достаточно для публикации и прохождения."""
    if test.tickets and all(hasattr(t, "questions") for t in test.tickets):
        return bool(complete_tickets(test))
    t = (
        db.query(Test)
        .options(selectinload(Test.tickets).selectinload(Ticket.questions))
        .filter(Test.id == test.id)
        .one()
    )
    return bool(complete_tickets(t))


def test_is_available(db: Session, test: Test) -> bool:
    """Тест доступен для экзамена/тренировки: опубликован и есть хотя бы один готовый билет."""
    return bool(test.published) and test_is_ready_to_take(db, test)


def count_tickets(db: Session, test_id: int) -> int:
    return db.query(Ticket).filter(Ticket.test_id == test_id).count()


def assert_can_add_ticket(db: Session, test_id: int) -> None:
    if count_tickets(db, test_id) >= MAX_TICKETS_PER_TEST:
        raise ValueError(f"В тесте не больше {MAX_TICKETS_PER_TEST} билетов.")
