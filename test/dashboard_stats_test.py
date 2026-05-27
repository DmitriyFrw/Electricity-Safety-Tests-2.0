
from __future__ import annotations
import datetime as dt
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app.attempt_service import score_attempt
from app.constants import (
    DEFAULT_SAFETY_GROUP, DEFAULT_SAFETY_GROUP_DESC,
    KNOWLEDGE_CHECK_INTERVAL_DAYS, MAX_ERRORS_DISPLAY, MIN_PASS_PERCENT,
)
from app.database import get_db
from app.auth import get_current_user  # Замените на вашу зависимость авторизации
from app.models import Attempt, Test, User
from app.validation import test_is_ready_to_take


router = APIRouter()

def _serialize_attempt(db: Session, attempt: Attempt) -> dict:
    s = score_attempt(db, attempt)
    return {
        "test_title": attempt.test.title if attempt.test else "Удалённый тест",
        "date": attempt.finished_at.strftime("%d.%m.%Y %H:%M") if attempt.finished_at else "",
        "correct": s.correct,
        "total": s.total,
        "errors": s.errors,
        "percent": s.percent,
        "grade": s.grade,
        "grade_class": s.grade_class,
    }

@router.get("/api/cabinet/stats")
def get_cabinet_stats(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ctx = build_dashboard_context(db, user)

    # Сериализация дат
    if ctx["materials_updated"]:
        ctx["materials_updated"] = ctx["materials_updated"].strftime("%d.%m.%Y")
    if ctx["last_test_date"]:
        ctx["last_test_date"] = ctx["last_test_date"].strftime("%d.%m.%Y")
    if ctx["next_check_date"]:
        d = ctx["next_check_date"]
        months = ['', 'января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
        weekdays = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
        ctx["next_check_date"] = d.strftime("%d.%m.%Y")
        ctx["next_check_month"] = months[d.month]
        ctx["next_check_weekday"] = weekdays[d.weekday()]

    # Таблицы 
    created_tests = db.query(Test).filter(Test.author_id == user.id).options(selectinload(Test.tickets)).order_by(Test.created_at.desc()).all()
    ctx["created_tests"] = [
        {
            "id": t.id, "title": t.title,
            "tickets_count": len(t.tickets),
            "created_at": t.created_at.strftime("%d.%m.%Y")
        } for t in created_tests
    ]

    attempts = db.query(Attempt).options(selectinload(Attempt.test)).filter(Attempt.user_id == user.id, Attempt.finished_at.isnot(None)).order_by(Attempt.finished_at.desc()).limit(50).all()
    ctx["attempt_rows"] = [_serialize_attempt(db, a) for a in attempts]

    return ctx