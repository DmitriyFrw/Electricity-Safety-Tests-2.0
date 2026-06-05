from __future__ import annotations

from typing import Literal

from app.form_requests.base import FormRequest
from app.schemas import UpdateUserRoleIn


class UpdateUserRoleRequest(FormRequest):
    role: Literal["admin", "ezh", "kot"]

    @classmethod
    def from_body(cls, body: UpdateUserRoleIn) -> UpdateUserRoleRequest:
        return cls.model_validate(body.model_dump())
