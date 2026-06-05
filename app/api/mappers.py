from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.services.attempts.scoring import AttemptScore, score_attempt

from app.constants import (
    DEFAULT_SAFETY_GROUP,
    DEFAULT_SAFETY_GROUP_DESC,
    EXAM_TICKET_TIME_LIMIT_SECONDS,
    MAX_TICKETS_PER_TEST,
    MIN_PASS_PERCENT,
    QUESTIONS_PER_TICKET,
    ROLE_ADMIN,
)
from app.dashboard_stats import build_dashboard_context, display_name
from app.models import Attempt, SignedProtocol, Test, Ticket, User
from app.roles import can_create_tests, can_edit_test, role_label
from app.support.profile import is_profile_complete

from app.schemas import (
    AttemptRowOut,
    CreatedTestOut,
    DashboardOut,
    AdminProtocolDraftUserOut,
    StaffProtocolExportOut,
    ExamPaperOut,
    ExamResultOut,
    ExamSessionOut,
    ExamTicketPaperOut,
    QuestionEditOut,
    QuestionExamOut,
    SignedProtocolOut,
    TestEditOut,
    TestListItemOut,
    TestListOut,
    TicketEditOut,
    TicketExamOut,
    TicketResultRowOut,
    UserAdminOut,
    UserOut,
)
from app.services.attempts.scoring import attempt_to_row
from app.support.profile import is_profile_complete
from app.support.validation import test_is_ready_to_take, ticket_is_complete


def user_out(user: User) -> UserOut:
    dn = display_name(user)
    return UserOut(
        id=user.id,
        username=user.username,
        display_name=dn,
        role=user.role,
        role_label=role_label(user.role),
        can_create_tests=can_create_tests(user),
        safety_group=DEFAULT_SAFETY_GROUP,
        safety_group_desc=DEFAULT_SAFETY_GROUP_DESC,
        full_name=user.full_name,
        birth_date=user.birth_date,
        job_title=user.job_title,
        business_unit=user.business_unit,
        profile_complete=is_profile_complete(user),
    )


def user_admin_out(user: User) -> UserAdminOut:
    return UserAdminOut(
        id=user.id,
        username=user.username,
        display_name=display_name(user),
        role=user.role,
        role_label=role_label(user.role),
        created_at=user.created_at,
        profile_complete=is_profile_complete(user),
    )


def _admin_protocol_drafts(db: Session, user: User, *, limit: int = 25) -> list[AdminProtocolDraftUserOut]:
    from app.repositories import UserRepository

    if user.role != ROLE_ADMIN:
        return []
    rows: list[AdminProtocolDraftUserOut] = []
    for u in UserRepository.list_all(db):
        if not is_profile_complete(u):
            continue
        rows.append(
            AdminProtocolDraftUserOut(
                user_id=u.id,
                username=u.username,
                display_name=display_name(u),
                profile_complete=True,
            )
        )
        if len(rows) >= limit:
            break
    rows.sort(key=lambda r: r.display_name.casefold())
    return rows


def _staff_protocol_exports(db: Session, user: User, *, limit: int = 15) -> list[StaffProtocolExportOut]:
    from app.repositories import AttemptRepository

    if not can_create_tests(user):
        return []
    rows: list[StaffProtocolExportOut] = []
    for attempt in AttemptRepository.list_finished_exam_for_staff(db, user, limit=limit * 4):
        summary = score_attempt(db, attempt)
        if summary.percent < MIN_PASS_PERCENT:
            continue
        examinee = attempt.user
        if examinee is None:
            continue
        rows.append(
            StaffProtocolExportOut(
                attempt_id=attempt.id,
                test_id=attempt.test_id,
                test_title=attempt.test.title if attempt.test else "",
                examinee_full_name=str(examinee.full_name or examinee.username or "").strip(),
                percent=float(summary.percent),
                profile_complete=is_profile_complete(examinee),
            )
        )
        if len(rows) >= limit:
            break
    return rows


def dashboard_out(
    db: Session,
    user: User,
    *,
    created_tests: list[Test],
    attempts: list[Attempt],
    signed_protocol: SignedProtocol | None = None,
) -> DashboardOut:
    base = build_dashboard_context(
        db, user, attempts=attempts, created_tests_count=len(created_tests)
    )
    attempt_rows = []
    for a in attempts:
        row = attempt_to_row(db, a)
        attempt_rows.append(
            AttemptRowOut(
                attempt_id=a.id,
                test_id=a.test_id,
                test_title=row["test"].title if row["test"] else "",
                finished_at=a.finished_at,  # type: ignore[arg-type]
                correct=row["correct"],
                total=row["total"],
                percent=row["percent"],
                errors=row["errors"],
                grade=row["grade"],
                grade_class=row["grade_class"],
            )
        )
    return DashboardOut(
        user=user_out(user),
        can_create_tests=can_create_tests(user),
        tickets_count=base["tickets_count"],
        exam_test_id=base["exam_test_id"],
        min_pass_percent=base["min_pass_percent"],
        max_errors_allowed=base["max_errors_allowed"],
        materials_updated=base["materials_updated"],
        last_percent=base["last_percent"],
        last_errors=base["last_errors"],
        last_grade=base["last_grade"],
        last_grade_class=base["last_grade_class"],
        last_test_title=base["last_test_title"],
        last_test_date=base["last_test_date"],
        next_check_date=base["next_check_date"],
        signed_protocol=(
            SignedProtocolOut(
                attempt_id=signed_protocol.attempt_id,
                test_id=signed_protocol.attempt.test_id if signed_protocol.attempt else 0,
                signer_id=signed_protocol.signer_id,
                signer_username=signed_protocol.signer.username if signed_protocol.signer else "",
                examinee_id=signed_protocol.examinee_id,
                examinee_full_name=signed_protocol.examinee_full_name,
                examinee_birth_date=signed_protocol.examinee_birth_date,
                examinee_job_title=signed_protocol.examinee_job_title,
                test_title=signed_protocol.test_title,
                result_percent=signed_protocol.result_percent,
                signed_at=signed_protocol.signed_at,
            )
            if signed_protocol
            else None
        ),
        staff_protocol_exports=_staff_protocol_exports(db, user),
        admin_protocol_drafts=_admin_protocol_drafts(db, user),
        created_tests=[
            CreatedTestOut(
                id=t.id,
                title=t.title,
                ticket_count=len(t.tickets),
                created_at=t.created_at,
            )
            for t in created_tests
        ],
        attempts=attempt_rows,
    )


def test_list_out(db: Session, tests: list[Test], current_user: User) -> TestListOut:
    items = []
    for t in tests:
        items.append(
            TestListItemOut(
                id=t.id,
                title=t.title,
                description=t.description,
                author_id=t.author_id,
                author_username=t.author.username if t.author else "",
                ticket_count=len(t.tickets),
                ready=test_is_ready_to_take(db, t),
                can_edit=can_edit_test(current_user, t),
            )
        )
    return TestListOut(items=items)


def _ticket_exam_out(ticket: Ticket) -> TicketExamOut:
    qs = [
        QuestionExamOut(
            id=q.id,
            position=q.position,
            text=q.text,
            option_a=q.option_a,
            option_b=q.option_b,
            option_c=q.option_c,
            option_d=q.option_d,
        )
        for q in sorted(ticket.questions, key=lambda x: x.position)
    ]
    return TicketExamOut(
        id=ticket.id,
        position=ticket.position,
        title=ticket.title,
        option_count=ticket.option_count,
        questions=qs,
    )


def exam_paper_out(test: Test) -> ExamPaperOut:
    tickets = [_ticket_exam_out(ticket) for ticket in sorted(test.tickets, key=lambda x: x.position)]
    return ExamPaperOut(
        id=test.id,
        title=test.title,
        min_pass_percent=MIN_PASS_PERCENT,
        tickets=tickets,
    )


def exam_session_out(
    *,
    attempt_id: int,
    test: Test,
    completed_ticket_ids: list[int],
    next_ticket_id: int | None,
) -> ExamSessionOut:
    return ExamSessionOut(
        attempt_id=attempt_id,
        test_id=test.id,
        test_title=test.title,
        ticket_count=len(test.tickets),
        completed_ticket_ids=completed_ticket_ids,
        next_ticket_id=next_ticket_id,
        time_limit_seconds=EXAM_TICKET_TIME_LIMIT_SECONDS,
    )


def exam_ticket_paper_out(
    *,
    test: Test,
    attempt_id: int,
    ticket: Ticket,
    ticket_index: int,
    seconds_remaining: int,
    deadline_at: datetime,
) -> ExamTicketPaperOut:
    return ExamTicketPaperOut(
        test_id=test.id,
        test_title=test.title,
        attempt_id=attempt_id,
        ticket=_ticket_exam_out(ticket),
        ticket_index=ticket_index,
        ticket_count=len(test.tickets),
        min_pass_percent=MIN_PASS_PERCENT,
        time_limit_seconds=EXAM_TICKET_TIME_LIMIT_SECONDS,
        seconds_remaining=seconds_remaining,
        deadline_at=deadline_at,
    )


def exam_result_out(
    test: Test,
    summary: AttemptScore,
    ticket_rows: list[dict[str, Any]],
    *,
    attempt_id: int,
    protocol_signed: bool = False,
) -> ExamResultOut:
    return ExamResultOut(
        attempt_id=attempt_id,
        test_id=test.id,
        test_title=test.title,
        correct=summary.correct,
        total=summary.total,
        percent=summary.percent,
        errors=summary.errors,
        grade=summary.grade,
        grade_class=summary.grade_class,
        passed_exam=summary.percent >= MIN_PASS_PERCENT,
        protocol_signed=protocol_signed,
        min_pass_percent=MIN_PASS_PERCENT,
        ticket_rows=[
            TicketResultRowOut(
                n=int(r["n"]),
                correct=int(r["correct"]),
                total=int(r["total"]),
                percent=float(r["percent"]),
                grade=str(r["grade"]),
                grade_class=str(r["grade_class"]),
            )
            for r in ticket_rows
        ],
    )


def test_edit_out(db: Session, test: Test) -> TestEditOut:
    tickets = []
    for ticket in sorted(test.tickets, key=lambda x: x.position):
        qs = [
            QuestionEditOut(
                id=q.id,
                position=q.position,
                text=q.text,
                correct_index=q.correct_index,
                option_a=q.option_a,
                option_b=q.option_b,
                option_c=q.option_c,
                option_d=q.option_d,
            )
            for q in sorted(ticket.questions, key=lambda x: x.position)
        ]
        tickets.append(
            TicketEditOut(
                id=ticket.id,
                position=ticket.position,
                title=ticket.title,
                option_count=ticket.option_count,
                complete=ticket_is_complete(ticket),
                questions=qs,
            )
        )
    return TestEditOut(
        id=test.id,
        title=test.title,
        description=test.description,
        ready=test_is_ready_to_take(db, test),
        max_tickets=MAX_TICKETS_PER_TEST,
        questions_per_ticket=QUESTIONS_PER_TICKET,
        tickets=tickets,
    )
