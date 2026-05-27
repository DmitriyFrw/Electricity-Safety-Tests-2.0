from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.csrf import get_or_create_csrf_token
from app.database import get_db
from app.deps import get_current_user_optional, login_required
from app.exceptions import AppError
from app.form_requests.auth import LoginRequest, RegisterRequest
from app.models import User
from app.schemas import CsrfOut, MessageOut, UserOut
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/csrf", response_model=CsrfOut)
def auth_csrf(request: Request):
    return CsrfOut(csrf_token=get_or_create_csrf_token(request))


@router.get("/me", response_model=Optional[UserOut])
def auth_me(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
):
    user = get_current_user_optional(request, db)
    if not user:
        return None
    from app.api_serializers import user_out

    return user_out(user)


@router.post("/register", response_model=UserOut)
def auth_register(
    form: RegisterRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return AuthService.register(db, request, form)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e


@router.post("/login", response_model=UserOut)
def auth_login(
    form: LoginRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return AuthService.login(db, request, form)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e


@router.post("/logout", response_model=MessageOut)
def auth_logout(request: Request):
    request.session.clear()
    get_or_create_csrf_token(request)
    return MessageOut(message="Вы вышли из системы")


@router.get("/session", response_model=UserOut)
def auth_session(user: Annotated[User, Depends(login_required)]):
    from app.api_serializers import user_out

    return user_out(user)
