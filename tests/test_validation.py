from __future__ import annotations

from app.models import Question, Test, Ticket
from app.support import validation as validation_rules


def _complete_ticket(ticket_id: int, test_id: int, position: int) -> Ticket:
    ticket = Ticket(id=ticket_id, test_id=test_id, position=position, option_count=4)
    ticket.questions = [
        Question(
            id=ticket_id * 100 + pos,
            ticket_id=ticket_id,
            position=pos,
            text="Вопрос",
            correct_index=0,
            correct_indexes="0",
            option_count=4,
            option_a="A",
            option_b="B",
            option_c="C",
            option_d="D",
        )
        for pos in range(1, 11)
    ]
    return ticket


def _incomplete_ticket(ticket_id: int, test_id: int, position: int) -> Ticket:
    ticket = Ticket(id=ticket_id, test_id=test_id, position=position, option_count=4)
    ticket.questions = [
        Question(
            id=ticket_id * 100 + 1,
            ticket_id=ticket_id,
            position=1,
            text="Вопрос",
            correct_index=0,
            correct_indexes="0",
            option_count=4,
            option_a="A",
            option_b="B",
            option_c="C",
            option_d="D",
        )
    ]
    return ticket


def test_ready_requires_every_ticket_complete():
    test = Test(id=1, author_id=1, title="T", safety_group="II")
    test.tickets = [
        _complete_ticket(1, 1, 1),
        _incomplete_ticket(2, 1, 2),
    ]
    assert not validation_rules.test_is_ready_loaded(test)

    test.tickets[1] = _complete_ticket(2, 1, 2)
    assert validation_rules.test_is_ready_loaded(test)


def test_ready_false_without_tickets():
    test = Test(id=2, author_id=1, title="Empty", safety_group="II")
    test.tickets = []
    assert not validation_rules.test_is_ready_loaded(test)


def test_ready_to_take_loads_tickets_from_db(db_session):
    from app.models import User

    author = User(username="val_author", password_hash="x", role="ezh")
    db_session.add(author)
    db_session.flush()
    test = Test(author_id=author.id, title="DB", safety_group="II")
    db_session.add(test)
    db_session.flush()
    complete = _complete_ticket(1, test.id, 1)
    incomplete = _incomplete_ticket(2, test.id, 2)
    db_session.add_all([complete, incomplete])
    db_session.commit()

    reloaded = Test(id=test.id, author_id=author.id, title="DB", safety_group="II")
    assert not validation_rules.test_is_ready_to_take(db_session, reloaded)
