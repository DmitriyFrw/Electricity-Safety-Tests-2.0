from __future__ import annotations

from app.api.mappers import user_out
from app.constants import DEFAULT_KOT_SAFETY_GROUP, ROLE_KOT
from app.cqrs.messages.auth import LoginUserCommand, RegisterUserCommand
from app.dto import AuditEventDTO
from app.models import User
from app.repositories import UserRepository
from app.schemas import UserOut
from app.services.security import LoginRateLimiter, SecurityAuditService
from app.support.errors import AppError
from app.support.passwords import hash_password, verify_password


class RegisterUserHandler:
    def handle(self, command: RegisterUserCommand) -> UserOut:
        db, http, form = command.db, command.http, command.form
        if UserRepository.get_by_username(db, form.username):
            SecurityAuditService.log(
                AuditEventDTO(
                    action="register",
                    actor_id=None,
                    actor_username=form.username,
                    success=False,
                    ip=http.client_ip,
                    details="username already exists",
                )
            )
            raise AppError("Такой логин уже занят", status_code=400)

        user = User(
            username=form.username,
            password_hash=hash_password(form.password),
            role=ROLE_KOT,
            safety_group=DEFAULT_KOT_SAFETY_GROUP,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        http.session.set("user_id", user.id)
        SecurityAuditService.log(
            AuditEventDTO(
                action="register",
                actor_id=user.id,
                actor_username=user.username,
                success=True,
                ip=http.client_ip,
            )
        )
        return user_out(user)


class LoginUserHandler:
    def handle(self, command: LoginUserCommand) -> UserOut:
        db, http, form = command.db, command.http, command.form
        ip = http.client_ip
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
        http.session.set("user_id", user.id)
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
