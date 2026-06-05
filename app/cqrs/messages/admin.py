from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.cqrs.base import Command, Query
from app.form_requests.admin import UpdateUserRoleRequest
from app.models import User


@dataclass(frozen=True, slots=True)
class ListUsersQuery(Query):
    db: Session


@dataclass(frozen=True, slots=True)
class UpdateUserRoleCommand(Command):
    db: Session
    actor: User
    target_user_id: int
    form: UpdateUserRoleRequest


@dataclass(frozen=True, slots=True)
class GetUserProtocolDraftPdfQuery(Query):
    db: Session
    actor: User
    target_user_id: int
