from __future__ import annotations

from sqlalchemy.orm import Session

from app.api.mappers import exam_session_out, exam_ticket_paper_out
from app.form_requests.tests import SubmitExamRequest
from app.models import Attempt, Ticket, User
from app.repositories import AttemptRepository
from app.services.exams.result import build_exam_result_out
from app.services.exams.session import (
    completed_ticket_ids,
    create_exam_attempt,
    finish_exam_attempt,
    get_exam_composition,
    next_exam_ticket_id,
    start_ticket_for_exam,
    submit_exam_ticket,
    ticket_deadline,
)
from app.support.exam_composition import load_exam_questions
from app.support.exam_ticket_order import ticket_index_in_order
from app.services.tests._common import get_test_or_raise, require_test_ready
from app.support.errors import AppError
from app.schemas import ExamResultOut, ExamSessionOut, ExamTicketPaperOut


class TestExamService:
    @staticmethod
    def _session_out(db: Session, test, attempt: Attempt) -> ExamSessionOut:
        done = set(completed_ticket_ids(db, attempt))
        composition = get_exam_composition(db, attempt, test)
        next_id = next_exam_ticket_id(composition, done)
        return exam_session_out(
            attempt_id=attempt.id,
            test=test,
            completed_ticket_ids=sorted(done),
            next_ticket_id=next_id,
            random_ticket_order=True,
        )

    @staticmethod
    def start_exam_session(db: Session, test_id: int, user: User) -> ExamSessionOut:
        test = get_test_or_raise(db, test_id)
        require_test_ready(test, user, db)
        try:
            attempt = create_exam_attempt(db, user_id=user.id, test_id=test.id, test=test)
        except ValueError as e:
            raise AppError(str(e), status_code=400) from e
        return TestExamService._session_out(db, test, attempt)

    @staticmethod
    def get_exam_session(db: Session, test_id: int, user: User) -> ExamSessionOut:
        test = get_test_or_raise(db, test_id)
        attempt = AttemptRepository.get_open_exam(db, user_id=user.id, test_id=test_id)
        if not attempt:
            raise AppError("Нет активной экзаменационной сессии", status_code=404)
        return TestExamService._session_out(db, test, attempt)

    @staticmethod
    def get_exam_ticket(
        db: Session, test_id: int, ticket_id: int, user: User
    ) -> ExamTicketPaperOut:
        test = get_test_or_raise(db, test_id)
        require_test_ready(test, user, db)
        attempt = AttemptRepository.get_open_exam(db, user_id=user.id, test_id=test_id)
        if not attempt:
            raise AppError("Сначала начните экзамен", status_code=400)
        composition = get_exam_composition(db, attempt, test)
        if ticket_id != composition.ticket_id:
            raise AppError("Билет не найден", status_code=404)
        ticket = db.get(Ticket, composition.ticket_id)
        if not ticket:
            raise AppError("Билет не найден", status_code=404)
        try:
            ta, remaining = start_ticket_for_exam(
                db, attempt=attempt, ticket=ticket, composition=composition
            )
        except ValueError as e:
            raise AppError(str(e), status_code=408) from e
        questions = load_exam_questions(db, composition.question_ids)
        ticket_index = ticket_index_in_order(composition, ticket.id)
        return exam_ticket_paper_out(
            test=test,
            attempt_id=attempt.id,
            ticket=ticket,
            ticket_index=ticket_index,
            seconds_remaining=remaining,
            deadline_at=ticket_deadline(ta.started_at),
            questions=questions,
        )

    @staticmethod
    def submit_exam_ticket_answers(
        db: Session, test_id: int, ticket_id: int, user: User, form: SubmitExamRequest
    ) -> ExamSessionOut:
        test = get_test_or_raise(db, test_id)
        attempt = AttemptRepository.get_open_exam(db, user_id=user.id, test_id=test_id)
        if not attempt:
            raise AppError("Нет активной экзаменационной сессии", status_code=400)
        composition = get_exam_composition(db, attempt, test)
        if ticket_id != composition.ticket_id:
            raise AppError("Билет не найден", status_code=404)
        ticket = db.get(Ticket, composition.ticket_id)
        if not ticket:
            raise AppError("Билет не найден", status_code=404)
        try:
            submit_exam_ticket(
                db,
                attempt=attempt,
                ticket=ticket,
                composition=composition,
                answers=form.answers_map(),
            )
        except ValueError as e:
            raise AppError(str(e), status_code=408) from e
        return TestExamService._session_out(db, test, attempt)

    @staticmethod
    def finish_exam(db: Session, test_id: int, user: User) -> ExamResultOut:
        test = get_test_or_raise(db, test_id)
        attempt = AttemptRepository.get_open_exam(db, user_id=user.id, test_id=test_id)
        if not attempt:
            raise AppError("Нет активной экзаменационной сессии", status_code=400)
        try:
            finish_exam_attempt(db, attempt=attempt, test=test)
        except ValueError as e:
            raise AppError(str(e), status_code=400) from e
        return build_exam_result_out(db, attempt=attempt, test=test)
