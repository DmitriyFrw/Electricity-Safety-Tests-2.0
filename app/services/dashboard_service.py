from __future__ import annotations

from sqlalchemy.orm import Session

from app.cqrs.bus import dispatch_query
from app.cqrs.messages.dashboard import GetDashboardQuery
from app.models import User
from app.schemas import DashboardOut


class DashboardService:
    @staticmethod
    def get_dashboard(db: Session, user: User) -> DashboardOut:
        return dispatch_query(GetDashboardQuery(db=db, user=user), DashboardOut)
