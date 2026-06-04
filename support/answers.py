from __future__ import annotations

"""Нормализация ответов: A–D или 1–4 → индекс 0..3."""

LABEL_TO_INDEX = {"A": 0, "B": 1, "C": 2, "D": 3, "1": 0, "2": 1, "3": 2, "4": 3}
INDEX_TO_LETTER = {0: "A", 1: "B", 2: "C", 3: "D"}
INDEX_TO_DIGIT = {0: "1", 1: "2", 2: "3", 3: "4"}


def parse_answer_label(raw: str | None) -> int | None:
    if raw is None:
        return None
    s = str(raw).strip().upper()
    if s in LABEL_TO_INDEX:
        return LABEL_TO_INDEX[s]
    return None
