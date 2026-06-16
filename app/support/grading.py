from __future__ import annotations

from app.constants import (
    GRADE_EXCELLENT_MIN_PERCENT,
    GRADE_GOOD_MIN_PERCENT,
    MIN_PASS_PERCENT,
)


def score_percent(correct: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return 100.0 * correct / total


def grade_for_percent(pct: float) -> str:
    if pct < MIN_PASS_PERCENT:
        return "неудовлетворительно"
    if pct < GRADE_GOOD_MIN_PERCENT:
        return "удовлетворительно"
    if pct < GRADE_EXCELLENT_MIN_PERCENT:
        return "хорошо"
    return "отлично"


def exam_is_passed(pct: float) -> bool:
    """Экзамен сдан при оценке удовлетворительно, хорошо или отлично."""
    return pct >= MIN_PASS_PERCENT


def grade_for_exam_protocol(pct: float) -> str:
    """Оценка в протоколе PDF (неудовлетворительно — экзамен не сдан)."""
    return grade_for_percent(pct)


def grade_css_class(pct: float) -> str:
    if pct < MIN_PASS_PERCENT:
        return "grade-bad"
    if pct < GRADE_GOOD_MIN_PERCENT:
        return "grade-ok"
    if pct < GRADE_EXCELLENT_MIN_PERCENT:
        return "grade-good"
    return "grade-excellent"
