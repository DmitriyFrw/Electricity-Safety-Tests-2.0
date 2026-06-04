from __future__ import annotations

from pydantic import BaseModel, ValidationError


class FormRequest(BaseModel):
    """
    Аналог Laravel FormRequest: Pydantic-модель с правилами валидации.
    Контроллер получает уже провалидированный объект через Depends(...).
    """

    model_config = {"str_strip_whitespace": True}

    @classmethod
    def from_body(cls, body: BaseModel) -> "FormRequest":
        """Создать FormRequest из «сырого» тела (schemas.*)."""
        return cls.model_validate(body.model_dump())
