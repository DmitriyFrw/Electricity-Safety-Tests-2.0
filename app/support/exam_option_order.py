from __future__ import annotations

from sqlalchemy.orm import Session, selectinload

from app.models import Attempt, Question, Test
from app.support.exam_composition import ExamComposition, load_exam_questions
from app.support.question_option_order import (
    OptionOrders,
    build_option_orders_for_questions,
    parse_option_orders,
    serialize_option_orders,
)


def _question_source_test(question: Question) -> Test | None:
    ticket = getattr(question, "ticket", None)
    if ticket is None:
        return None
    return getattr(ticket, "test", None)


def ensure_exam_option_orders(
    db: Session,
    attempt: Attempt,
    composition: ExamComposition,
) -> OptionOrders:
    questions = load_exam_questions(
        db,
        composition.question_ids,
        load_test=True,
    )
    expected_ids = {q.id for q in questions}
    existing = parse_option_orders(attempt.question_option_orders) or {}
    if existing and expected_ids.issubset(existing.keys()):
        return {qid: existing[qid] for qid in expected_ids if qid in existing}

    orders = build_option_orders_for_questions(
        questions,
        should_shuffle=lambda q: bool(
            (source_test := _question_source_test(q)) and source_test.random_option_order
        ),
    )
    merged = {**existing, **orders}
    attempt.question_option_orders = serialize_option_orders(merged) if merged else None
    return {qid: merged[qid] for qid in expected_ids if qid in merged}
