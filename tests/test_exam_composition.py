from __future__ import annotations

import random

from app.constants import QUESTIONS_PER_TICKET
from app.models import Attempt, Question, Test, Ticket
from app.support.exam_composition import (
    ExamComposition,
    build_random_exam_composition,
    ensure_exam_composition,
    parse_composition,
    serialize_composition,
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


def test_build_random_exam_composition_picks_questions_from_group(db_session):
    author_id = 1
    test_a = Test(author_id=author_id, title="A", safety_group="II", published=True)
    test_b = Test(author_id=author_id, title="B", safety_group="II", published=True)
    _add_complete_ticket(test_a, 1, marker="A")
    _add_complete_ticket(test_b, 1, marker="B")
    db_session.add_all([test_a, test_b])
    db_session.commit()

    composition = build_random_exam_composition(db_session, "II")
    assert len(composition.question_ids) == QUESTIONS_PER_TICKET
    pool_ids = {q.id for t in test_a.tickets + test_b.tickets for q in t.questions}
    assert all(qid in pool_ids for qid in composition.question_ids)
    assert composition.ticket_id in {t.id for t in test_a.tickets + test_b.tickets}


def test_ensure_exam_composition_persists_attempt(db_session, monkeypatch):
    test = Test(author_id=1, title="T", safety_group="II", published=True)
    _add_complete_ticket(test, 1, marker="T")
    db_session.add(test)
    db_session.commit()

    monkeypatch.setattr(random, "choice", lambda xs: xs[0])
    monkeypatch.setattr(random, "sample", lambda pool, k: pool[:k])

    attempt = Attempt(user_id=1, test_id=test.id, mode="exam")
    db_session.add(attempt)
    db_session.flush()

    composition = ensure_exam_composition(db_session, attempt, "II")
    assert composition == parse_composition(attempt.exam_ticket_order)
    assert len(composition.question_ids) == QUESTIONS_PER_TICKET


def test_serialize_parse_roundtrip():
    raw = serialize_composition(ExamComposition(ticket_id=5, question_ids=[1, 2, 3]))
    parsed = parse_composition(raw)
    assert parsed is not None
    assert parsed.ticket_id == 5
    assert parsed.question_ids == [1, 2, 3]
