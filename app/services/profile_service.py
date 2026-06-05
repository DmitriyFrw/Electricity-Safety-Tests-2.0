from __future__ import annotations

from sqlalchemy.orm import Session

from app.cqrs.bus import dispatch_command, dispatch_query
from app.cqrs.messages.profile import (
    BuildProtocolPdfQuery,
    GetProfileQuery,
    StartAttemptsExportCommand,
    StartProtocolExportCommand,
    UpdateProfileCommand,
)
from app.form_requests.profile import ProfileUpdateRequest
from app.models import User
from app.schemas import UserOut


class ProfileService:
    @staticmethod
    def get_profile(user: User) -> UserOut:
        return dispatch_query(GetProfileQuery(user=user), UserOut)

    @staticmethod
    def update_profile(db: Session, user: User, form: ProfileUpdateRequest) -> UserOut:
        return dispatch_command(UpdateProfileCommand(db=db, user=user, form=form), UserOut)

    @staticmethod
    def build_protocol_pdf(db: Session, user: User) -> bytes:
        return dispatch_query(BuildProtocolPdfQuery(db=db, user=user), bytes)

    @staticmethod
    def build_protocol_pdf_async(db: Session, user: User) -> str:
        return dispatch_command(StartProtocolExportCommand(db=db, user=user), str)

    @staticmethod
    def export_attempts_async(user: User, test_id: int | None = None) -> str:
        return dispatch_command(
            StartAttemptsExportCommand(user=user, test_id=test_id), str
        )
