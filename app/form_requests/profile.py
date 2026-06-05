from __future__ import annotations

import datetime as dt

from pydantic import Field, field_validator

from app.constants import ALLOWED_BUSINESS_UNITS
from app.form_requests.base import FormRequest


class ProfileUpdateRequest(FormRequest):
    full_name: str = Field(min_length=1, max_length=200)
    birth_date: dt.date
    job_title: str = Field(min_length=1, max_length=200)
    business_unit: str = Field(min_length=1, max_length=32)

    @field_validator("full_name", "job_title")
    @classmethod
    def strip_required(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Поле не может быть пустым")
        return s

    @field_validator("birth_date")
    @classmethod
    def birth_date_not_future(cls, v: dt.date) -> dt.date:
        if v > dt.date.today():
            raise ValueError("Дата рождения не может быть в будущем")
        return v

    @field_validator("business_unit")
    @classmethod
    def validate_business_unit(cls, v: str) -> str:
        s = v.strip()
        if s not in ALLOWED_BUSINESS_UNITS:
            raise ValueError("Выберите юридическое лицо из списка")
        return s
