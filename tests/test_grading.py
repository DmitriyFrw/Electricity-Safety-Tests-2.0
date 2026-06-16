from __future__ import annotations

from app.constants import (
    GRADE_EXCELLENT_MIN_PERCENT,
    GRADE_GOOD_MIN_PERCENT,
    MIN_PASS_PERCENT,
)
from app.support.grading import exam_is_passed, grade_css_class, grade_for_percent


def test_grade_bands_use_constants():
    assert grade_for_percent(MIN_PASS_PERCENT - 0.1) == "неудовлетворительно"
    assert grade_for_percent(MIN_PASS_PERCENT) == "удовлетворительно"
    assert grade_for_percent(GRADE_GOOD_MIN_PERCENT - 0.1) == "удовлетворительно"
    assert grade_for_percent(GRADE_GOOD_MIN_PERCENT) == "хорошо"
    assert grade_for_percent(GRADE_EXCELLENT_MIN_PERCENT - 0.1) == "хорошо"
    assert grade_for_percent(GRADE_EXCELLENT_MIN_PERCENT) == "отлично"


def test_exam_is_passed_for_satisfactory_and_above():
    assert not exam_is_passed(MIN_PASS_PERCENT - 0.1)
    assert exam_is_passed(MIN_PASS_PERCENT)
    assert exam_is_passed(GRADE_GOOD_MIN_PERCENT - 0.1)
    assert exam_is_passed(90)
    assert exam_is_passed(100)


def test_grade_css_class_follows_same_thresholds():
    assert grade_css_class(MIN_PASS_PERCENT - 1) == "grade-bad"
    assert grade_css_class(MIN_PASS_PERCENT) == "grade-ok"
    assert grade_css_class(GRADE_GOOD_MIN_PERCENT) == "grade-good"
    assert grade_css_class(GRADE_EXCELLENT_MIN_PERCENT) == "grade-excellent"
