from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import login_required
from app.models import User
from app.schemas import DashboardOut
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardOut)
def get_dashboard(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
):
    return DashboardService.get_dashboard(db, user)
