from __future__ import annotations

import re

from pydantic import Field, field_validator, model_validator

from app.form_requests.base import FormRequest

_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_.-]+$")


class RegisterRequest(FormRequest):
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=6, max_length=128)
    password2: str = Field(min_length=6, max_length=128)

    @field_validator("username")
    @classmethod
    def username_format(cls, v: str) -> str:
        u = v.strip()
        if not _USERNAME_RE.match(u):
            raise ValueError("Логин может содержать только буквы, цифры, _, . и -")
        return u

    @model_validator(mode="after")
    def passwords_match(self) -> RegisterRequest:
        if self.password != self.password2:
            raise ValueError("Пароли не совпадают")
        return self


class LoginRequest(FormRequest):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("username")
    @classmethod
    def strip_username(cls, v: str) -> str:
        return v.strip()
