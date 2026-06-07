from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.cqrs.base import Command, Query
from app.models import User
from app.schemas import UpdateKotSafetyGroupIn


@dataclass(frozen=True, slots=True)
class ListKotUsersQuery(Query):
    db: Session
    actor: User


@dataclass(frozen=True, slots=True)
class UpdateKotSafetyGroupCommand(Command):
    db: Session
    actor: User
    target_user_id: int
    form: UpdateKotSafetyGroupIn
