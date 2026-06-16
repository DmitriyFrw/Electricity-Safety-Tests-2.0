from __future__ import annotations

from types import SimpleNamespace

from app.support.question_option_order import (
    build_option_orders_for_questions,
    remap_answers_map,
    remap_display_answer_raw,
    shuffled_option_fields,
)


def test_shuffled_option_fields_keep_question_options_isolated():
    question = SimpleNamespace(
        id=1,
        option_count=4,
        option_a="A1",
        option_b="B1",
        option_c="C1",
        option_d="D1",
        ticket=None,
    )
    permutation = [2, 0, 3, 1]
    shuffled = shuffled_option_fields(question, permutation)
    assert shuffled == {
        "option_a": "C1",
        "option_b": "A1",
        "option_c": "D1",
        "option_d": "B1",
    }


def test_remap_display_answer_to_storage_index():
    permutation = [2, 0, 3, 1]
    assert remap_display_answer_raw("B", permutation, option_count=4) == "A"
    assert remap_display_answer_raw("A", permutation, option_count=4) == "C"


def test_build_option_orders_only_for_flagged_questions():
    q1 = SimpleNamespace(id=1, option_count=3, ticket=SimpleNamespace(test=SimpleNamespace(random_option_order=True)))
    q2 = SimpleNamespace(id=2, option_count=4, ticket=SimpleNamespace(test=SimpleNamespace(random_option_order=False)))
    orders = build_option_orders_for_questions(
        [q1, q2],
        should_shuffle=lambda q: bool(q.ticket.test.random_option_order),
    )
    assert set(orders.keys()) == {1}
    assert len(orders[1]) == 3


def test_remap_answers_map_per_question():
    q1 = SimpleNamespace(id=1, option_count=4, ticket=None)
    q2 = SimpleNamespace(id=2, option_count=4, ticket=None)
    orders = {1: [1, 0, 2, 3], 2: [3, 2, 1, 0]}
    remapped = remap_answers_map({1: "A", 2: "A"}, orders, {1: q1, 2: q2})
    assert remapped[1] == "B"
    assert remapped[2] == "D"
