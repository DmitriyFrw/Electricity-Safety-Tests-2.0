from __future__ import annotations

from sqlalchemy.orm import Session

from app.adapters.http_context import HttpContext
from app.cqrs.bus import dispatch_command
from app.cqrs.messages.auth import LoginUserCommand, RegisterUserCommand
from app.form_requests.auth import LoginRequest, RegisterRequest
from app.schemas import UserOut


class AuthService:
    @staticmethod
    def register(db: Session, http: HttpContext, form: RegisterRequest) -> UserOut:
        return dispatch_command(RegisterUserCommand(db=db, http=http, form=form), UserOut)

    @staticmethod
    def login(db: Session, http: HttpContext, form: LoginRequest) -> UserOut:
        return dispatch_command(LoginUserCommand(db=db, http=http, form=form), UserOut)
