from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.cqrs.base import Command, Query
from app.form_requests.profile import ProfileUpdateRequest
from app.models import User


@dataclass(frozen=True, slots=True)
class GetProfileQuery(Query):
    user: User


@dataclass(frozen=True, slots=True)
class UpdateProfileCommand(Command):
    db: Session
    user: User
    form: ProfileUpdateRequest


@dataclass(frozen=True, slots=True)
class BuildProtocolPdfQuery(Query):
    db: Session
    user: User


@dataclass(frozen=True, slots=True)
class StartProtocolExportCommand(Command):
    db: Session
    user: User


@dataclass(frozen=True, slots=True)
class StartAttemptsExportCommand(Command):
    user: User
    test_id: int | None = None
