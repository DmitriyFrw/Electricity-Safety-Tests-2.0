from __future__ import annotations

from app.constants import MAX_OPTION_COUNT, MIN_OPTION_COUNT
from app.models import Question, Ticket

OPTION_LABELS: tuple[str, ...] = ("A", "B", "C", "D")


def normalize_option_count(value: int | None) -> int:
    if value is None:
        return MAX_OPTION_COUNT
    return max(MIN_OPTION_COUNT, min(MAX_OPTION_COUNT, int(value)))


def ticket_option_count(ticket: Ticket) -> int:
    return normalize_option_count(getattr(ticket, "option_count", None))


def question_option_count(question: Question) -> int:
    own = getattr(question, "option_count", None)
    if own is not None:
        return normalize_option_count(own)
    ticket = getattr(question, "ticket", None)
    if ticket is not None:
        return ticket_option_count(ticket)
    return MAX_OPTION_COUNT


def question_option_values(question: Question, count: int) -> list[str]:
    n = normalize_option_count(count)
    values = [question.option_a, question.option_b, question.option_c, question.option_d]
    return values[:n]


def clamp_correct_index(index: int, count: int) -> int:
    n = normalize_option_count(count)
    if index < 0:
        return 0
    if index >= n:
        return n - 1
    return index


def clear_unused_options(question: Question, count: int) -> None:
    n = normalize_option_count(count)
    if n < 4:
        question.option_d = ""
    if n < 3:
        question.option_c = ""
