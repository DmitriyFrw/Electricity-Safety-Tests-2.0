from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.adapters.http_context import HttpContext
from app.cqrs.base import Command
from app.form_requests.auth import LoginRequest, RegisterRequest


@dataclass(frozen=True, slots=True)
class RegisterUserCommand(Command):
    db: Session
    http: HttpContext
    form: RegisterRequest


@dataclass(frozen=True, slots=True)
class LoginUserCommand(Command):
    db: Session
    http: HttpContext
    form: LoginRequest
