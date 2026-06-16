from __future__ import annotations

import datetime as dt
from collections import defaultdict
from typing import Any

from sqlalchemy.orm import Session

from app.constants import ATTEMPT_MODE_EXAM
from app.dashboard_stats import display_name
from app.models import Attempt, Test
from app.repositories import AttemptRepository, UserRepository
from app.services.attempts.scoring import AttemptScore, score_attempt
from app.support.exam_completion import exam_attempt_is_passed
from app.support.grading import grade_for_percent


def build_admin_stats(db: Session) -> dict[str, Any]:
    users_count = len(UserRepository.list_all(db))
    tests_count = db.query(Test).count()
    attempts = AttemptRepository.list_finished_all(db, limit=2000)

    grade_counts: dict[str, int] = defaultdict(int)
    monthly: dict[tuple[int, int], list[float]] = defaultdict(list)
    total_percent = 0.0
    exams_passed = 0
    scored: list[tuple[Attempt, AttemptScore]] = []

    for attempt in attempts:
        score = score_attempt(db, attempt)
        scored.append((attempt, score))
        grade = grade_for_percent(score.percent)
        grade_counts[grade] += 1
        total_percent += score.percent

        if attempt.finished_at:
            key = (attempt.finished_at.year, attempt.finished_at.month)
            monthly[key].append(score.percent)

        if attempt.mode == ATTEMPT_MODE_EXAM and exam_attempt_is_passed(db, attempt, score.percent):
            exams_passed += 1

    scored_total = len(scored)
    average_percent = round(total_percent / scored_total, 1) if scored_total else 0.0

    distribution_grades = ("удовлетворительно", "хорошо", "отлично", "неудовлетворительно")
    grade_distribution = []
    for g in distribution_grades:
        count = grade_counts.get(g, 0)
        share = round(100.0 * count / scored_total, 1) if scored_total else 0.0
        grade_distribution.append({"grade": g, "count": count, "percent": share})

    today = dt.date.today()
    month_keys: list[tuple[int, int]] = []
    cursor = today.replace(day=1)
    for _ in range(6):
        month_keys.append((cursor.year, cursor.month))
        cursor = (cursor - dt.timedelta(days=1)).replace(day=1)
    month_keys.reverse()

    monthly_results = []
    for year, month in month_keys:
        values = monthly.get((year, month), [])
        monthly_results.append(
            {
                "year": year,
                "month": month,
                "average_percent": round(sum(values) / len(values), 1) if values else 0.0,
                "attempt_count": len(values),
            }
        )

    recent = []
    for attempt, score in scored[:10]:
        user = attempt.user
        recent.append(
            {
                "user_display_name": display_name(user) if user else "Пользователь",
                "test_title": attempt.test.title if attempt.test else "Тест",
                "percent": score.percent,
                "grade": score.grade,
                "finished_at": attempt.finished_at,
            }
        )

    return {
        "users_count": users_count,
        "tests_count": tests_count,
        "exams_passed_count": exams_passed,
        "average_percent": average_percent,
        "grade_distribution": grade_distribution,
        "monthly_results": monthly_results,
        "recent_activity": recent,
    }
