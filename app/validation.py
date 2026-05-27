from sqlalchemy.orm import Session, selectinload

from app.constants import MAX_TICKETS_PER_TEST, QUESTIONS_PER_TICKET
from app.models import Test, Ticket

_EXPECTED_POSITIONS = frozenset(range(1, QUESTIONS_PER_TICKET + 1))


def ticket_is_complete(ticket: Ticket) -> bool:
    qs = sorted(ticket.questions, key=lambda q: q.position)
    if len(qs) != QUESTIONS_PER_TICKET:
        return False
    positions = {q.position for q in qs}
    if positions != _EXPECTED_POSITIONS:
        return False
    for q in qs:
        if q.correct_index not in (0, 1, 2, 3):
            return False
        if not (q.text or "").strip():
            return False
        for opt in (q.option_a, q.option_b, q.option_c, q.option_d):
            if not (opt or "").strip():
                return False
    return True


def test_is_ready_loaded(test: Test) -> bool:
    """Проверка готовности теста по уже загруженным билетам (без доп. запросов)."""
    if not test.tickets:
        return False
    return all(ticket_is_complete(ticket) for ticket in test.tickets)


def test_is_ready_to_take(db: Session, test: Test) -> bool:
    if test.tickets and all(hasattr(t, "questions") and t.questions for t in test.tickets):
        return test_is_ready_loaded(test)
    t = (
        db.query(Test)
        .options(selectinload(Test.tickets).selectinload(Ticket.questions))
        .filter(Test.id == test.id)
        .one()
    )
    if not t.tickets:
        return False
    return all(ticket_is_complete(ticket) for ticket in t.tickets)


def count_tickets(db: Session, test_id: int) -> int:
    return db.query(Ticket).filter(Ticket.test_id == test_id).count()


def assert_can_add_ticket(db: Session, test_id: int) -> None:
    if count_tickets(db, test_id) >= MAX_TICKETS_PER_TEST:
        raise ValueError(f"В тесте не больше {MAX_TICKETS_PER_TEST} билетов.")
