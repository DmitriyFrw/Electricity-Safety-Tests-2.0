from __future__ import annotations

from pydantic import Field, field_validator, model_validator

from app.constants import QUESTIONS_PER_TICKET
from app.form_requests.base import FormRequest


class TestCreateRequest(FormRequest):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        t = v.strip()
        if not t:
            raise ValueError("Укажите название")
        return t

    @field_validator("description")
    @classmethod
    def normalize_description(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None


class QuestionSaveRequest(FormRequest):
    position: int = Field(ge=1, le=QUESTIONS_PER_TICKET)
    text: str = Field(max_length=5000)
    option_a: str = Field(max_length=2000)
    option_b: str = Field(max_length=2000)
    option_c: str = Field(max_length=2000)
    option_d: str = Field(max_length=2000)
    correct: str = Field(min_length=1, max_length=1)


class TicketSaveRequest(FormRequest):
    questions: list[QuestionSaveRequest]

    @model_validator(mode="after")
    def exact_question_count(self) -> TicketSaveRequest:
        if len(self.questions) != QUESTIONS_PER_TICKET:
            raise ValueError(f"Нужно ровно {QUESTIONS_PER_TICKET} вопросов")
        positions = {q.position for q in self.questions}
        expected = set(range(1, QUESTIONS_PER_TICKET + 1))
        if positions != expected:
            raise ValueError(f"Позиции вопросов должны быть 1..{QUESTIONS_PER_TICKET}")
        return self


class AnswerItemRequest(FormRequest):
    question_id: int = Field(gt=0)
    value: str = Field(min_length=1, max_length=8)


class SubmitExamRequest(FormRequest):
    answers: list[AnswerItemRequest] = Field(default_factory=list)

    def answers_map(self) -> dict[int, str]:
        return {a.question_id: a.value for a in self.answers}
