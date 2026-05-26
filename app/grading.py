from __future__ import annotations

# Текстовая оценка (отдельно от порога сдачи MIN_PASS_PERCENT в app.constants).


def score_percent(correct: int, total: int) -> float:
    """Доля правильных ответов в процентах (0..100)."""
    if total <= 0:
        return 0.0
    return 100.0 * correct / total


def grade_for_percent(pct: float) -> str:
    """
    Оценка по доле правильных ответов:
    <75% — неудовлетворительно; 75–85% (вкл. 75, до 85) — удовлетворительно;
    85–95% — хорошо; от 95% — отлично.
    """
    if pct < 75:
        return "неудовлетворительно"
    if pct < 85:
        return "удовлетворительно"
    if pct < 95:
        return "хорошо"
    return "отлично"


def grade_css_class(pct: float) -> str:
    """Класс для оформления строки оценки."""
    if pct < 75:
        return "grade-bad"
    if pct < 85:
        return "grade-ok"
    if pct < 95:
        return "grade-good"
    return "grade-excellent"
