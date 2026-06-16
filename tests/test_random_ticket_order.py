from __future__ import annotations

import random

from app.constants import QUESTIONS_PER_TICKET
from app.models import Attempt, Question, Test, Ticket
from app.support.exam_composition import build_exam_composition, ensure_exam_composition
from app.support.exam_ticket_order import (
    ensure_training_ticket_order,
    parse_ticket_id_order,
    pick_exam_source_ticket,
)


def _add_complete_ticket(test: Test, position: int, *, marker: str) -> Ticket:
    ticket = Ticket(position=position, option_count=4)
    for pos in range(1, QUESTIONS_PER_TICKET + 1):
        ticket.questions.append(
            Question(
                position=pos,
                text=f"{marker}-{pos}",
                correct_index=0,
                option_a="A",
                option_b="B",
                option_c="C",
                option_d="D",
            )
        )
    test.tickets.append(ticket)
    return ticket


def test_pick_exam_source_ticket_uses_first_when_random_disabled():
    test = Test(author_id=1, title="T", safety_group="II", published=True, random_ticket_order=False)
    first = _add_complete_ticket(test, 1, marker="A")
    _add_complete_ticket(test, 2, marker="B")
    group = list(test.tickets)

    picked = pick_exam_source_ticket(test, group_tickets=group)
    assert picked.id == first.id


def test_pick_exam_source_ticket_shuffles_when_random_enabled(monkeypatch):
    test = Test(author_id=1, title="T", safety_group="II", published=True, random_ticket_order=True)
    _add_complete_ticket(test, 1, marker="A")
    second = _add_complete_ticket(test, 2, marker="B")
    group = list(test.tickets)

    monkeypatch.setattr(random, "choice", lambda xs: xs[1])
    picked = pick_exam_source_ticket(test, group_tickets=group)
    assert picked.id == second.id


def test_build_exam_composition_respects_random_ticket_order(db_session, monkeypatch):
    test = Test(
        author_id=1,
        title="T",
        safety_group="II",
        published=True,
        random_ticket_order=False,
    )
    first = _add_complete_ticket(test, 1, marker="A")
    _add_complete_ticket(test, 2, marker="B")
    db_session.add(test)
    db_session.commit()

    monkeypatch.setattr(random, "sample", lambda pool, k: pool[:k])

    composition = build_exam_composition(db_session, test)
    assert composition.ticket_id == first.id
    assert len(composition.question_ids) == QUESTIONS_PER_TICKET


def test_ensure_training_ticket_order_shuffles_when_enabled(db_session, monkeypatch):
    test = Test(
        author_id=1,
        title="T",
        safety_group="II",
        published=True,
        random_ticket_order=True,
    )
    _add_complete_ticket(test, 1, marker="A")
    _add_complete_ticket(test, 2, marker="B")
    db_session.add(test)
    db_session.commit()

    monkeypatch.setattr(random, "shuffle", lambda xs: xs.reverse())

    attempt = Attempt(user_id=1, test_id=test.id, mode="training")
    db_session.add(attempt)
    db_session.flush()

    order = ensure_training_ticket_order(db_session, attempt, test)
    assert order == [test.tickets[1].id, test.tickets[0].id]
    assert parse_ticket_id_order(attempt.exam_ticket_order) == order


def test_ensure_training_ticket_order_sorted_when_disabled(db_session):
    test = Test(
        author_id=1,
        title="T",
        safety_group="II",
        published=True,
        random_ticket_order=False,
    )
    _add_complete_ticket(test, 1, marker="A")
    _add_complete_ticket(test, 2, marker="B")
    db_session.add(test)
    db_session.commit()

    attempt = Attempt(user_id=1, test_id=test.id, mode="training")
    db_session.add(attempt)
    db_session.flush()

    order = ensure_training_ticket_order(db_session, attempt, test)
    assert order == [test.tickets[0].id, test.tickets[1].id]
    assert attempt.exam_ticket_order is None


def test_ensure_exam_composition_uses_test_settings(db_session, monkeypatch):
    test = Test(
        author_id=1,
        title="T",
        safety_group="II",
        published=True,
        random_ticket_order=False,
    )
    first = _add_complete_ticket(test, 1, marker="A")
    _add_complete_ticket(test, 2, marker="B")
    db_session.add(test)
    db_session.commit()

    monkeypatch.setattr(random, "sample", lambda pool, k: pool[:k])

    attempt = Attempt(user_id=1, test_id=test.id, mode="exam")
    db_session.add(attempt)
    db_session.flush()

    composition = ensure_exam_composition(db_session, attempt, test)
    assert composition.ticket_id == first.id
