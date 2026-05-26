from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, selectinload

from app.api_serializers import dashboard_out
from app.database import get_db
from app.deps import login_required
from app.models import Attempt, Test, User
from app.schemas import DashboardOut

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardOut)
def get_dashboard(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
):
    created = (
        db.query(Test)
        .options(selectinload(Test.tickets))
        .filter(Test.author_id == user.id)
        .order_by(Test.created_at.desc())
        .all()
    )
    attempts = (
        db.query(Attempt)
        .options(selectinload(Attempt.test), selectinload(Attempt.user_answers))
        .filter(Attempt.user_id == user.id, Attempt.finished_at.isnot(None))
        .order_by(Attempt.finished_at.desc())
        .limit(100)
        .all()
    )
    return dashboard_out(db, user, created_tests=created, attempts=attempts)
