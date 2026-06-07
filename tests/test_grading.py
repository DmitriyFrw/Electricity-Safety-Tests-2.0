from __future__ import annotations

from app.support.grading import exam_is_passed, grade_for_percent


def test_exam_is_passed_for_satisfactory_and_above():
    assert grade_for_percent(74) == "неудовлетворительно"
    assert not exam_is_passed(74)
    assert exam_is_passed(75)
    assert exam_is_passed(84.9)
    assert exam_is_passed(90)
    assert exam_is_passed(100)
