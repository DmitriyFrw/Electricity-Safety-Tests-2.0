from __future__ import annotations

from fastapi import Request
from sqlalchemy.orm import Session

from app.api_serializers import user_out
from app.auth_utils import hash_password, verify_password
from app.constants import ROLE_KOT
from app.csrf import rotate_csrf_token
from app.exceptions import AppError
from app.form_requests.auth import LoginRequest, RegisterRequest
from app.models import User
from app.repositories import UserRepository
from app.schemas import UserOut
from app.services.security import LoginRateLimiter, SecurityAuditService
from app.dto import AuditEventDTO


class AuthService:
    @staticmethod
    def register(db: Session, request: Request, form: RegisterRequest) -> UserOut:
        if UserRepository.get_by_username(db, form.username):
            SecurityAuditService.log(
                AuditEventDTO(
                    action="register",
                    actor_id=None,
                    actor_username=form.username,
                    success=False,
                    ip=request.client.host if request.client else None,
                    details="username already exists",
                )
            )
            raise AppError("Такой логин уже занят", status_code=400)

        user = User(
            username=form.username,
            password_hash=hash_password(form.password),
            role=ROLE_KOT,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        request.session["user_id"] = user.id
        rotate_csrf_token(request)
        SecurityAuditService.log(
            AuditEventDTO(
                action="register",
                actor_id=user.id,
                actor_username=user.username,
                success=True,
                ip=request.client.host if request.client else None,
            )
        )
        return user_out(user)

    @staticmethod
    def login(db: Session, request: Request, form: LoginRequest) -> UserOut:
        ip = request.client.host if request.client else None
        if LoginRateLimiter.is_blocked(username=form.username, ip=ip):
            SecurityAuditService.log(
                AuditEventDTO(
                    action="login",
                    actor_id=None,
                    actor_username=form.username,
                    success=False,
                    ip=ip,
                    details="rate limit exceeded",
                )
            )
            raise AppError("Слишком много неудачных попыток входа. Попробуйте позже.", status_code=429)
        user = UserRepository.get_by_username(db, form.username)
        if not user or not verify_password(form.password, user.password_hash):
            LoginRateLimiter.register_failure(username=form.username, ip=ip)
            SecurityAuditService.log(
                AuditEventDTO(
                    action="login",
                    actor_id=user.id if user else None,
                    actor_username=form.username,
                    success=False,
                    ip=ip,
                    details="invalid credentials",
                )
            )
            raise AppError("Неверный логин или пароль", status_code=400)
        LoginRateLimiter.reset(username=form.username, ip=ip)
        request.session["user_id"] = user.id
        rotate_csrf_token(request)
        SecurityAuditService.log(
            AuditEventDTO(
                action="login",
                actor_id=user.id,
                actor_username=user.username,
                success=True,
                ip=ip,
            )
        )
        return user_out(user)
