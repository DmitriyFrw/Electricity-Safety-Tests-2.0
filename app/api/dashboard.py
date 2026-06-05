from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import login_required
from app.cqrs.bus import dispatch_query
from app.cqrs.messages.dashboard import GetDashboardQuery
from app.database import get_db
from app.models import User
from app.schemas import DashboardOut

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardOut)
def get_dashboard(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
) -> DashboardOut:
    return dispatch_query(GetDashboardQuery(db=db, user=user), DashboardOut)
