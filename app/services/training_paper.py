from __future__ import annotations

from sqlalchemy.orm import Session

from app.constants import ATTEMPT_MODE_TRAINING
from app.models import Attempt, Test
from app.repositories import AttemptRepository
from app.support.question_option_order import (
    OptionOrders,
    build_option_orders_for_test,
    parse_option_orders,
    serialize_option_orders,
)
from app.support.exam_ticket_order import ensure_training_ticket_order
from app.support.validation import complete_tickets_sorted


def _question_ids_for_test(test: Test) -> set[int]:
    return {q.id for ticket in complete_tickets_sorted(test) for q in ticket.questions}


def ensure_training_paper_attempt(
    db: Session, *, user_id: int, test: Test
) -> tuple[Attempt, OptionOrders, list[int]]:
    existing = AttemptRepository.get_open_training(db, user_id=user_id, test_id=test.id)
    if existing:
        orders = _sync_training_option_orders(db, attempt=existing, test=test)
        ticket_ids = ensure_training_ticket_order(db, existing, test)
        return existing, orders, ticket_ids

    attempt = Attempt(
        user_id=user_id,
        test_id=test.id,
        mode=ATTEMPT_MODE_TRAINING,
        finished_at=None,
    )
    db.add(attempt)
    db.flush()
    orders = build_option_orders_for_test(test) if test.random_option_order else {}
    attempt.question_option_orders = serialize_option_orders(orders) if orders else None
    ticket_ids = ensure_training_ticket_order(db, attempt, test)
    db.commit()
    db.refresh(attempt)
    return attempt, orders, ticket_ids


def _sync_training_option_orders(db: Session, *, attempt: Attempt, test: Test) -> OptionOrders:
    expected = _question_ids_for_test(test)
    if not test.random_option_order:
        if attempt.question_option_orders is not None:
            attempt.question_option_orders = None
            db.commit()
        return {}

    existing = parse_option_orders(attempt.question_option_orders) or {}
    if existing and expected.issubset(existing.keys()):
        return existing

    orders = build_option_orders_for_test(test)
    attempt.question_option_orders = serialize_option_orders(orders) if orders else None
    db.commit()
    return orders
