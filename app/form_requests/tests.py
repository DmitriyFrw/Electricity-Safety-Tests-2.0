from __future__ import annotations

from pydantic import Field, field_validator, model_validator

from app.constants import MAX_OPTION_COUNT, MIN_OPTION_COUNT, QUESTIONS_PER_TICKET
from app.support.answers import parse_answer_labels
from app.support.question_options import OPTION_LABELS, normalize_option_count
from app.form_requests.base import FormRequest


class TestCreateRequest(FormRequest):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    safety_group: str = "II"

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

    @field_validator("safety_group")
    @classmethod
    def validate_safety_group(cls, v: str) -> str:
        from app.constants import SAFETY_GROUPS

        g = v.strip().upper()
        if g not in SAFETY_GROUPS:
            raise ValueError(f"Укажите группу: {', '.join(SAFETY_GROUPS)}")
        return g


class QuestionSaveRequest(FormRequest):
    position: int = Field(ge=1, le=QUESTIONS_PER_TICKET)
    text: str = Field(max_length=20000)
    option_a: str = Field(max_length=20000)
    option_b: str = Field(max_length=20000)
    option_c: str = Field(max_length=20000)
    option_d: str = Field(max_length=20000)
    correct: str = Field(min_length=1, max_length=16)
    option_count: int = Field(default=MAX_OPTION_COUNT, ge=MIN_OPTION_COUNT, le=MAX_OPTION_COUNT)

    @field_validator("option_count")
    @classmethod
    def validate_question_option_count(cls, v: int) -> int:
        return normalize_option_count(v)


class TicketSaveRequest(FormRequest):
    title: str | None = Field(default=None, max_length=200)
    option_count: int = Field(default=MAX_OPTION_COUNT, ge=MIN_OPTION_COUNT, le=MAX_OPTION_COUNT)
    questions: list[QuestionSaveRequest]

    @field_validator("title")
    @classmethod
    def normalize_title(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None

    @field_validator("option_count")
    @classmethod
    def validate_option_count(cls, v: int) -> int:
        return normalize_option_count(v)

    @model_validator(mode="after")
    def exact_question_count(self) -> TicketSaveRequest:
        n = len(self.questions)
        if n < 1 or n > QUESTIONS_PER_TICKET:
            raise ValueError(f"Нужно от 1 до {QUESTIONS_PER_TICKET} вопросов")
        positions = sorted(q.position for q in self.questions)
        expected = list(range(1, n + 1))
        if positions != expected:
            raise ValueError(f"Позиции вопросов должны быть 1..{n} без пропусков")
        for q in self.questions:
            count = normalize_option_count(q.option_count)
            allowed = set(OPTION_LABELS[:count])
            indices = parse_answer_labels(q.correct, option_count=count)
            labels = {OPTION_LABELS[i] for i in indices if i < len(OPTION_LABELS)}
            if not labels or not labels.issubset(allowed):
                raise ValueError(
                    f"Верные ответы вопроса {q.position} должны быть из {', '.join(sorted(allowed))}"
                )
        return self


class AnswerItemRequest(FormRequest):
    question_id: int = Field(gt=0)
    value: str = Field(min_length=1, max_length=16)


class SubmitExamRequest(FormRequest):
    answers: list[AnswerItemRequest] = Field(default_factory=list)

    def answers_map(self) -> dict[int, str]:
        return {a.question_id: a.value for a in self.answers}
