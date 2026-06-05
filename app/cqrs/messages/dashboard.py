from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.cqrs.base import Query
from app.models import User


@dataclass(frozen=True, slots=True)
class GetDashboardQuery(Query):
    db: Session
    user: User
