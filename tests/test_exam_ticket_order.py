from __future__ import annotations

from app.models import Attempt, Question, Test, Ticket
from app.support.exam_composition import ExamComposition
from app.support.exam_ticket_order import ensure_exam_ticket_order, ticket_index_in_order


def _make_ready_test() -> Test:
    test = Test(author_id=1, title="T", safety_group="II", published=True)
    ticket = Ticket(position=1, option_count=4)
    for pos in range(1, 11):
        ticket.questions.append(
            Question(
                position=pos,
                text=f"Q{pos}",
                correct_index=0,
                option_a="A",
                option_b="B",
                option_c="C",
                option_d="D",
            )
        )
    test.tickets.append(ticket)
    return test


def test_ensure_exam_ticket_order_returns_single_composition(db_session):
    test = _make_ready_test()
    db_session.add(test)
    db_session.commit()
    attempt = Attempt(user_id=1, test_id=test.id, mode="exam")
    db_session.add(attempt)
    db_session.flush()

    composition = ensure_exam_ticket_order(db_session, attempt, test)
    assert isinstance(composition, ExamComposition)
    assert composition.ticket_id == test.tickets[0].id
    assert len(composition.question_ids) == 10


def test_ticket_index_in_order_for_single_ticket():
    composition = ExamComposition(ticket_id=42, question_ids=[1, 2, 3])
    assert ticket_index_in_order(composition, 42) == 1
