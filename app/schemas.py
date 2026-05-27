from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserOut(BaseModel):
    id: int
    username: str
    display_name: str
    role: str
    role_label: str
    can_create_tests: bool
    safety_group: str
    safety_group_desc: str
    full_name: Optional[str] = None
    birth_date: Optional[date] = None
    job_title: Optional[str] = None


class ProfileUpdateIn(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    birth_date: date
    job_title: str = Field(min_length=1, max_length=200)


class ManualOut(BaseModel):
    id: str
    title: str
    filename: str


class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=6)
    password2: str = Field(min_length=6)


class LoginIn(BaseModel):
    username: str
    password: str


class MessageOut(BaseModel):
    message: str


class CsrfOut(BaseModel):
    csrf_token: str


class ErrorOut(BaseModel):
    detail: str


class AttemptRowOut(BaseModel):
    attempt_id: int
    test_id: int
    test_title: str
    finished_at: datetime
    correct: int
    total: int
    percent: float
    errors: int
    grade: str
    grade_class: str


class CreatedTestOut(BaseModel):
    id: int
    title: str
    ticket_count: int
    created_at: datetime


class DashboardOut(BaseModel):
    user: UserOut
    can_create_tests: bool
    tickets_count: int
    exam_test_id: Optional[int]
    min_pass_percent: int
    max_errors_allowed: int
    materials_updated: Optional[datetime]
    last_percent: Optional[float]
    last_errors: Optional[int]
    last_grade: Optional[str]
    last_grade_class: Optional[str]
    last_test_title: Optional[str]
    last_test_date: Optional[datetime]
    next_check_date: date
    created_tests: list[CreatedTestOut]
    attempts: list[AttemptRowOut]


class TestListItemOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    author_id: int
    author_username: str
    ticket_count: int
    ready: bool
    can_edit: bool


class TestListOut(BaseModel):
    items: list[TestListItemOut]


class TestCreateIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None


class TestCreateOut(BaseModel):
    id: int
    title: str


class QuestionExamOut(BaseModel):
    id: int
    position: int
    text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str


class TicketExamOut(BaseModel):
    id: int
    position: int
    questions: list[QuestionExamOut]


class ExamPaperOut(BaseModel):
    id: int
    title: str
    min_pass_percent: int
    tickets: list[TicketExamOut]


class ExamSessionOut(BaseModel):
    attempt_id: int
    test_id: int
    test_title: str
    ticket_count: int
    completed_ticket_ids: list[int]
    next_ticket_id: Optional[int]
    time_limit_seconds: int


class ExamTicketPaperOut(BaseModel):
    test_id: int
    test_title: str
    attempt_id: int
    ticket: TicketExamOut
    ticket_index: int
    ticket_count: int
    min_pass_percent: int
    time_limit_seconds: int
    seconds_remaining: int
    deadline_at: datetime


class AnswerItemIn(BaseModel):
    question_id: int
    value: str


class SubmitExamIn(BaseModel):
    answers: list[AnswerItemIn]


class TicketResultRowOut(BaseModel):
    n: int
    correct: int
    total: int
    percent: float
    grade: str
    grade_class: str


class ExamResultOut(BaseModel):
    test_id: int
    test_title: str
    correct: int
    total: int
    percent: float
    errors: int
    grade: str
    grade_class: str
    passed_exam: bool
    min_pass_percent: int
    ticket_rows: list[TicketResultRowOut]


class QuestionEditOut(BaseModel):
    id: int
    position: int
    text: str
    correct_index: int
    option_a: str
    option_b: str
    option_c: str
    option_d: str


class TicketEditOut(BaseModel):
    id: int
    position: int
    complete: bool
    questions: list[QuestionEditOut]


class TestEditOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    ready: bool
    max_tickets: int
    questions_per_ticket: int
    tickets: list[TicketEditOut]


class QuestionSaveIn(BaseModel):
    position: int = Field(ge=1, le=10)
    text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct: str


class TicketSaveIn(BaseModel):
    questions: list[QuestionSaveIn]
