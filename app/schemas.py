from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from typing import Literal

from pydantic import BaseModel, Field


class UserOut(BaseModel):
    id: int
    username: str
    display_name: str
    role: str
    role_label: str
    can_create_tests: bool
    can_edit_wiki: bool
    safety_group: str
    safety_group_desc: str
    full_name: Optional[str] = None
    birth_date: Optional[date] = None
    job_title: Optional[str] = None
    business_unit: Optional[str] = None
    profile_complete: bool = False


class UserAdminOut(BaseModel):
    id: int
    username: str
    display_name: str
    role: str
    role_label: str
    safety_group: Optional[str] = None
    created_at: Optional[datetime] = None
    profile_complete: bool = False


class KotUserOut(BaseModel):
    id: int
    username: str
    display_name: str
    safety_group: str
    safety_group_desc: str
    profile_complete: bool = False


class UpdateUserRoleIn(BaseModel):
    """Тело PUT /api/admin/users/{user_id}/role (только роль admin)."""

    role: Literal["admin", "ezh", "kot"]


class UpdateKotSafetyGroupIn(BaseModel):
    safety_group: Literal["I", "II", "III", "IV"]


class ProfileUpdateIn(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    birth_date: date
    job_title: str = Field(min_length=1, max_length=200)
    business_unit: str = Field(min_length=1, max_length=32)


class ManualOut(BaseModel):
    id: str
    title: str
    filename: str


class WikiAttachmentOut(BaseModel):
    id: int
    filename: str
    mime_type: str
    size_bytes: int
    url: str
    is_image: bool


class WikiPageListItemOut(BaseModel):
    id: int
    title: str
    updated_at: datetime


class WikiPageOut(BaseModel):
    id: int
    title: str
    content: str
    updated_at: datetime
    attachments: list[WikiAttachmentOut]


class WikiPageCreateIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = ""


class WikiPageUpdateIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = ""


class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=6)
    password2: str = Field(min_length=6)


class LoginIn(BaseModel):
    username: str
    password: str


class MessageOut(BaseModel):
    message: str


class AsyncTaskAcceptedOut(BaseModel):
    task_id: str
    status: str


class AsyncTaskStatusOut(BaseModel):
    task_id: str
    status: str
    error: Optional[str] = None


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


class StaffProtocolExportOut(BaseModel):
    attempt_id: int
    test_id: int
    test_title: str
    examinee_full_name: str
    percent: float
    profile_complete: bool


class AdminProtocolDraftUserOut(BaseModel):
    user_id: int
    username: str
    display_name: str
    profile_complete: bool


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
    last_passed_exam_date: Optional[datetime] = None
    last_passed_exam_percent: Optional[float] = None
    last_passed_exam_grade: Optional[str] = None
    next_check_date: date
    signed_protocol: "SignedProtocolOut | None" = None
    staff_protocol_exports: list[StaffProtocolExportOut] = []
    admin_protocol_drafts: list[AdminProtocolDraftUserOut] = []
    created_tests: list[CreatedTestOut]
    attempts: list[AttemptRowOut]


class TestListItemOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    safety_group: str
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
    safety_group: Literal["I", "II", "III", "IV"] = "II"


class TestCreateOut(BaseModel):
    id: int
    title: str
    safety_group: str


class QuestionExamOut(BaseModel):
    id: int
    position: int
    text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    option_count: int = 4
    multiple_choice: bool = False


class TicketExamOut(BaseModel):
    id: int
    position: int
    title: Optional[str] = None
    option_count: int = 4
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
    random_ticket_order: bool = False


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
    value: str = Field(min_length=1, max_length=16)


class SubmitExamIn(BaseModel):
    answers: list[AnswerItemIn]


class TicketResultRowOut(BaseModel):
    n: int
    correct: int
    total: int
    percent: float
    grade: str
    grade_class: str


class QuestionResultOut(BaseModel):
    question_id: int
    ticket_id: int
    ticket_position: int
    ticket_title: Optional[str] = None
    question_position: int
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    option_count: int = 4
    correct_index: int
    correct_indexes: list[int] = Field(default_factory=list)
    selected_index: Optional[int] = None
    selected_indexes: list[int] = Field(default_factory=list)
    is_correct: bool


class ExamResultOut(BaseModel):
    attempt_id: int
    test_id: int
    test_title: str
    correct: int
    total: int
    percent: float
    errors: int
    grade: str
    grade_class: str
    passed_exam: bool
    protocol_signed: bool = False
    min_pass_percent: int
    ticket_rows: list[TicketResultRowOut]
    question_results: list[QuestionResultOut] = []


class SignedProtocolOut(BaseModel):
    attempt_id: int
    test_id: int
    signer_id: int
    signer_username: str
    examinee_id: int
    examinee_full_name: str
    examinee_birth_date: date
    examinee_job_title: str
    test_title: str
    result_percent: int
    signed_at: datetime


class QuestionEditOut(BaseModel):
    id: int
    position: int
    text: str
    correct_index: int
    correct_indexes: list[int] = Field(default_factory=list)
    option_count: int = 4
    option_a: str
    option_b: str
    option_c: str
    option_d: str


class TicketEditOut(BaseModel):
    id: int
    position: int
    title: Optional[str] = None
    option_count: int = 4
    complete: bool
    questions: list[QuestionEditOut]


class TestEditOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    safety_group: str
    published: bool = False
    content_complete: bool = False
    ready: bool
    max_tickets: int
    questions_per_ticket: int
    random_ticket_order: bool = False
    tickets: list[TicketEditOut]


class TestSettingsIn(BaseModel):
    random_ticket_order: bool


class QuestionSaveIn(BaseModel):
    position: int = Field(ge=1, le=10)
    text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct: str
    option_count: int = 4


class TicketSaveIn(BaseModel):
    title: Optional[str] = None
    option_count: int = 4
    questions: list[QuestionSaveIn]
