from __future__ import annotations

import re

from app.models import Question, UserAnswer

"""Нормалization ответов: A–D или 1–4 → индекс 0..3."""

LABEL_TO_INDEX = {"A": 0, "B": 1, "C": 2, "D": 3, "1": 0, "2": 1, "3": 2, "4": 3}
INDEX_TO_LETTER = {0: "A", 1: "B", 2: "C", 3: "D"}
INDEX_TO_DIGIT = {0: "1", 1: "2", 2: "3", 3: "4"}


def parse_answer_label(raw: str | None) -> int | None:
    labels = parse_answer_labels(raw)
    return labels[0] if labels else None


def parse_answer_labels(raw: str | None, *, option_count: int | None = None) -> list[int]:
    if raw is None or not str(raw).strip():
        return []
    s = str(raw).strip().upper()
    parts: list[str]
    if re.search(r"[,;\s]", s):
        parts = [p for p in re.split(r"[,;\s]+", s) if p.strip()]
    else:
        parts = list(s)
    indices: list[int] = []
    for part in parts:
        token = part.strip()
        if not token:
            continue
        idx = LABEL_TO_INDEX.get(token[0])
        if idx is not None:
            indices.append(idx)
    unique = sorted(set(indices))
    if option_count is not None and option_count > 0:
        max_i = option_count - 1
        unique = [i for i in unique if 0 <= i <= max_i]
    return unique


def encode_correct_indexes(indices: list[int]) -> str:
    unique = sorted({i for i in indices if i >= 0})
    if not unique:
        return "0"
    return ",".join(str(i) for i in unique)


def decode_correct_indexes(raw: str | None, *, fallback: int = 0) -> list[int]:
    if raw is None or not str(raw).strip():
        return [fallback]
    try:
        parsed = sorted({int(x.strip()) for x in str(raw).split(",") if x.strip() != ""})
    except ValueError:
        return [fallback]
    return parsed or [fallback]


def question_correct_indices(question: Question) -> list[int]:
    stored = getattr(question, "correct_indexes", None)
    if stored:
        return decode_correct_indexes(stored, fallback=question.correct_index)
    return [question.correct_index]


def question_allows_multiple(question: Question) -> bool:
    return len(question_correct_indices(question)) > 1


def format_answer_labels(indices: list[int]) -> str:
    if not indices:
        return "A"
    return ",".join(INDEX_TO_LETTER.get(i, "A") for i in sorted(set(indices)))


def user_answer_selected_indices(answer: UserAnswer) -> list[int]:
    stored = getattr(answer, "selected_indexes", None)
    if stored:
        fallback = answer.selected_index if answer.selected_index is not None else 0
        return decode_correct_indexes(stored, fallback=fallback)
    if answer.selected_index is not None:
        return [answer.selected_index]
    return []


def set_user_answer_from_raw(
    answer: UserAnswer,
    raw: str | None,
    *,
    option_count: int | None = None,
) -> list[int]:
    indices = parse_answer_labels(raw, option_count=option_count)
    if not indices:
        answer.selected_index = None
        answer.selected_indexes = None
        return []
    answer.selected_index = indices[0]
    answer.selected_indexes = encode_correct_indexes(indices) if len(indices) > 1 else None
    return indices


def is_answer_correct(selected: list[int], correct_indices: list[int]) -> bool:
    if not selected or not correct_indices:
        return False
    if len(correct_indices) > 1:
        return sorted(set(selected)) == sorted(set(correct_indices))
    return len(selected) == 1 and selected[0] == correct_indices[0]


def is_selected_answer_correct(selected_index: int | None, correct_indices: list[int]) -> bool:
    if selected_index is None:
        return False
    return is_answer_correct([selected_index], correct_indices)
