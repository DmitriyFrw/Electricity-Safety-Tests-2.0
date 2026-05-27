from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api_serializers import user_out
from app.auth_utils import hash_password, verify_password
from app.database import get_db
from app.deps import get_current_user_optional, login_required
from app.constants import ROLE_KOT
from app.csrf import get_or_create_csrf_token, rotate_csrf_token
from app.models import User
from app.schemas import CsrfOut, LoginIn, MessageOut, RegisterIn, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/csrf", response_model=CsrfOut)
def auth_csrf(request: Request):
    """Выдать CSRF-токен для заголовка X-CSRF-Token (без авторизации)."""
    return CsrfOut(csrf_token=get_or_create_csrf_token(request))


@router.get("/me", response_model=Optional[UserOut])
def auth_me(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
):
    user = get_current_user_optional(request, db)
    if not user:
        return None
    return user_out(user)


@router.post("/register", response_model=UserOut)
def auth_register(
    body: RegisterIn,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
):
    u = body.username.strip()
    if body.password != body.password2:
        raise HTTPException(status_code=400, detail="Пароли не совпадают")
    if db.query(User).filter(User.username == u).first():
        raise HTTPException(status_code=400, detail="Такой логин уже занят")
    user = User(username=u, password_hash=hash_password(body.password), role=ROLE_KOT)
    db.add(user)
    db.commit()
    db.refresh(user)
    request.session["user_id"] = user.id
    rotate_csrf_token(request)
    return user_out(user)


@router.post("/login", response_model=UserOut)
def auth_login(
    body: LoginIn,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
):
    u = body.username.strip()
    user = db.query(User).filter(User.username == u).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Неверный логин или пароль")
    request.session["user_id"] = user.id
    rotate_csrf_token(request)
    return user_out(user)


@router.post("/logout", response_model=MessageOut)
def auth_logout(request: Request):
    request.session.clear()
    get_or_create_csrf_token(request)
    return MessageOut(message="Вы вышли из системы")


@router.get("/session", response_model=UserOut)
def auth_session(user: Annotated[User, Depends(login_required)]):
    return user_out(user)
