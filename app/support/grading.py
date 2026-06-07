from __future__ import annotations

from app.constants import MIN_PASS_PERCENT

PASSING_EXAM_GRADES = frozenset({"удовлетворительно", "хорошо", "отлично"})


def score_percent(correct: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return 100.0 * correct / total


def grade_for_percent(pct: float) -> str:
    if pct < 75:
        return "неудовлетворительно"
    if pct < 85:
        return "удовлетворительно"
    if pct < 95:
        return "хорошо"
    return "отлично"


def exam_is_passed(pct: float) -> bool:
    """Экзамен сдан при оценке удовлетворительно, хорошо или отлично."""
    return grade_for_percent(pct) in PASSING_EXAM_GRADES


def grade_for_exam_protocol(pct: float) -> str:
    """Оценка в протоколе PDF (неудовлетворительно — экзамен не сдан)."""
    if not exam_is_passed(pct):
        return "неудовлетворительно"
    if pct < 85:
        return "удовлетворительно"
    if pct < 95:
        return "хорошо"
    return "отлично"


def grade_css_class(pct: float) -> str:
    if pct < 75:
        return "grade-bad"
    if pct < 85:
        return "grade-ok"
    if pct < 95:
        return "grade-good"
    return "grade-excellent"
