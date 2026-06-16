from __future__ import annotations

import json
import random
from typing import Callable, Mapping

from app.models import Question, Test
from app.support.answers import INDEX_TO_LETTER, parse_answer_labels
from app.support.question_options import question_option_count, question_option_values
from app.support.validation import complete_tickets_sorted

OptionOrders = dict[int, list[int]]
OPTION_FIELD_KEYS = ("option_a", "option_b", "option_c", "option_d")


def random_permutation(count: int, *, rng: random.Random | None = None) -> list[int]:
    n = max(1, int(count))
    indices = list(range(n))
    (rng or random).shuffle(indices)
    return indices


def serialize_option_orders(orders: OptionOrders) -> str:
    return json.dumps({str(k): v for k, v in orders.items()})


def parse_option_orders(raw: str | None) -> OptionOrders | None:
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    orders: OptionOrders = {}
    for key, value in data.items():
        try:
            qid = int(key)
        except (TypeError, ValueError):
            continue
        if not isinstance(value, list) or not value:
            continue
        if not all(isinstance(x, int) for x in value):
            continue
        orders[qid] = [int(x) for x in value]
    return orders or None


def build_option_orders_for_questions(
    questions: list[Question],
    *,
    should_shuffle: Callable[[Question], bool],
) -> OptionOrders:
    orders: OptionOrders = {}
    for question in questions:
        if not should_shuffle(question):
            continue
        count = question_option_count(question)
        orders[question.id] = random_permutation(count)
    return orders


def build_option_orders_for_test(test: Test) -> OptionOrders:
    questions = [q for ticket in complete_tickets_sorted(test) for q in ticket.questions]
    return build_option_orders_for_questions(questions, should_shuffle=lambda _q: True)


def shuffled_option_fields(question: Question, permutation: list[int]) -> dict[str, str]:
    count = question_option_count(question)
    values = question_option_values(question, count)
    shuffled = [values[i] for i in permutation if 0 <= i < len(values)]
    result = {key: "" for key in OPTION_FIELD_KEYS}
    for display_index, value in enumerate(shuffled):
        if display_index < len(OPTION_FIELD_KEYS):
            result[OPTION_FIELD_KEYS[display_index]] = value
    return result


def remap_display_indices_to_storage(display_indices: list[int], permutation: list[int]) -> list[int]:
    storage: list[int] = []
    for display_index in display_indices:
        if 0 <= display_index < len(permutation):
            storage.append(permutation[display_index])
    return sorted(set(storage))


def remap_display_answer_raw(
    raw: str | None,
    permutation: list[int],
    *,
    option_count: int,
) -> str | None:
    if raw is None or not str(raw).strip():
        return raw
    display_indices = parse_answer_labels(raw, option_count=option_count)
    storage_indices = remap_display_indices_to_storage(display_indices, permutation)
    if not storage_indices:
        return raw
    return ",".join(INDEX_TO_LETTER[i] for i in storage_indices)


def remap_answers_map(
    answers: Mapping[int, str],
    orders: OptionOrders,
    questions_by_id: Mapping[int, Question],
) -> dict[int, str]:
    remapped: dict[int, str] = {}
    for question_id, raw in answers.items():
        permutation = orders.get(question_id)
        question = questions_by_id.get(question_id)
        if not permutation or not question:
            remapped[question_id] = raw
            continue
        remapped[question_id] = remap_display_answer_raw(
            raw,
            permutation,
            option_count=question_option_count(question),
        ) or raw
    return remapped
