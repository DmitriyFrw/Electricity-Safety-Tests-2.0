from __future__ import annotations

import json
import random
from dataclasses import dataclass

from sqlalchemy.orm import Session, selectinload

from app.constants import QUESTIONS_PER_TICKET
from app.models import Attempt, Question, Test, Ticket
from app.support.validation import complete_tickets_sorted


@dataclass(frozen=True)
class ExamComposition:
    ticket_id: int
    question_ids: list[int]


def serialize_composition(composition: ExamComposition) -> str:
    return json.dumps(
        {"ticket_id": composition.ticket_id, "question_ids": composition.question_ids}
    )


def parse_composition(raw: str | None) -> ExamComposition | None:
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    ticket_id = data.get("ticket_id")
    question_ids = data.get("question_ids")
    if not isinstance(ticket_id, int):
        return None
    if not isinstance(question_ids, list) or not all(isinstance(x, int) for x in question_ids):
        return None
    if not question_ids:
        return None
    return ExamComposition(ticket_id=ticket_id, question_ids=question_ids)


def list_complete_tickets_for_safety_group(db: Session, safety_group: str) -> list[Ticket]:
    tests = (
        db.query(Test)
        .options(selectinload(Test.tickets).selectinload(Ticket.questions))
        .filter(Test.published.is_(True), Test.safety_group == safety_group)
        .all()
    )
    tickets: list[Ticket] = []
    for test in tests:
        tickets.extend(complete_tickets_sorted(test))
    return tickets


def _question_pool(tickets: list[Ticket]) -> list[Question]:
    pool: list[Question] = []
    for ticket in tickets:
        pool.extend(sorted(ticket.questions, key=lambda q: q.position))
    return pool


def build_random_exam_composition(db: Session, safety_group: str) -> ExamComposition:
    tickets = list_complete_tickets_for_safety_group(db, safety_group)
    if not tickets:
        raise ValueError("Нет готовых билетов для экзамена по этой группе")
    pool = _question_pool(tickets)
    if len(pool) < QUESTIONS_PER_TICKET:
        raise ValueError("Недостаточно вопросов для экзамена по этой группе")
    source_ticket = random.choice(tickets)
    selected = random.sample(pool, QUESTIONS_PER_TICKET)
    return ExamComposition(
        ticket_id=source_ticket.id,
        question_ids=[q.id for q in selected],
    )


def composition_is_valid(db: Session, composition: ExamComposition, safety_group: str) -> bool:
    ticket = db.get(Ticket, composition.ticket_id)
    if not ticket:
        return False
    test = db.get(Test, ticket.test_id)
    if not test or not test.published or test.safety_group != safety_group:
        return False
    if len(composition.question_ids) != QUESTIONS_PER_TICKET:
        return False
    tickets = list_complete_tickets_for_safety_group(db, safety_group)
    allowed_ids = {q.id for t in tickets for q in t.questions}
    return all(qid in allowed_ids for qid in composition.question_ids)


def ensure_exam_composition(db: Session, attempt: Attempt, safety_group: str) -> ExamComposition:
    existing = parse_composition(attempt.exam_ticket_order)
    if existing is not None and composition_is_valid(db, existing, safety_group):
        return existing
    composition = build_random_exam_composition(db, safety_group)
    attempt.exam_ticket_order = serialize_composition(composition)
    return composition


def load_exam_questions(db: Session, question_ids: list[int]) -> list[Question]:
    rows = (
        db.query(Question)
        .options(selectinload(Question.ticket))
        .filter(Question.id.in_(question_ids))
        .all()
    )
    by_id = {q.id: q for q in rows}
    return [by_id[qid] for qid in question_ids if qid in by_id]
