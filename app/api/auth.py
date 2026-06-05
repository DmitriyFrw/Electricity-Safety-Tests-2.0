from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.adapters.http_context import HttpContext
from app.api.deps import get_current_user_optional, login_required
from app.api.mappers import user_out
from app.csrf import get_or_create_csrf_token, rotate_csrf_token
from app.database import get_db
from app.form_requests.auth import LoginRequest, RegisterRequest
from app.models import User
from app.schemas import CsrfOut, MessageOut, UserOut
from app.services.users.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/csrf", response_model=CsrfOut)
def auth_csrf(request: Request) -> CsrfOut:
    return CsrfOut(csrf_token=get_or_create_csrf_token(request))


@router.get("/me", response_model=Optional[UserOut])
def auth_me(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> UserOut | None:
    user = get_current_user_optional(request, db)
    if not user:
        return None
    return user_out(user)


@router.post("/register", response_model=UserOut)
def auth_register(
    form: RegisterRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> UserOut:
    http = HttpContext.from_request(request)
    out = AuthService.register(db, http, form)
    rotate_csrf_token(request)
    return out


@router.post("/login", response_model=UserOut)
def auth_login(
    form: LoginRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> UserOut:
    http = HttpContext.from_request(request)
    out = AuthService.login(db, http, form)
    rotate_csrf_token(request)
    return out


@router.post("/logout", response_model=MessageOut)
def auth_logout(request: Request) -> MessageOut:
    request.session.clear()
    get_or_create_csrf_token(request)
    return MessageOut(message="Вы вышли из системы")


@router.get("/session", response_model=UserOut)
def auth_session(user: Annotated[User, Depends(login_required)]) -> UserOut:
    return user_out(user)
