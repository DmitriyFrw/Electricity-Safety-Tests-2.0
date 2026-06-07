from __future__ import annotations

from sqlalchemy.orm import Session

from app.api.mappers import exam_session_out, exam_ticket_paper_out
from app.cqrs.messages.tests import (
    FinishExamCommand,
    GetExamAttemptResultQuery,
    GetExamSessionQuery,
    OpenExamTicketCommand,
    StartExamSessionCommand,
    SubmitExamTicketAnswersCommand,
)
from app.models import Attempt, Test, Ticket
from app.repositories import AttemptRepository
from app.schemas import ExamResultOut, ExamSessionOut, ExamTicketPaperOut
from app.constants import ATTEMPT_MODE_EXAM
from app.roles import can_create_tests
from app.services.exams.result import build_exam_result_out
from app.services.attempts.scoring import score_attempt
from app.support.grading import exam_is_passed
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


def _session_out(db: Session, test: Test, attempt: Attempt) -> ExamSessionOut:
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


class StartExamSessionHandler:
    def handle(self, command: StartExamSessionCommand) -> ExamSessionOut:
        test = get_test_or_raise(command.db, command.test_id)
        require_test_ready(test, command.user, command.db)
        try:
            attempt = create_exam_attempt(
                command.db, user_id=command.user.id, test_id=test.id, test=test
            )
        except ValueError as e:
            raise AppError(str(e), status_code=400) from e
        return _session_out(command.db, test, attempt)


class GetExamSessionHandler:
    def handle(self, query: GetExamSessionQuery) -> ExamSessionOut:
        test = get_test_or_raise(query.db, query.test_id)
        attempt = AttemptRepository.get_open_exam(
            query.db, user_id=query.user.id, test_id=query.test_id
        )
        if not attempt:
            raise AppError("Нет активной экзаменационной сессии", status_code=404)
        return _session_out(query.db, test, attempt)


class OpenExamTicketHandler:
    def handle(self, command: OpenExamTicketCommand) -> ExamTicketPaperOut:
        test = get_test_or_raise(command.db, command.test_id)
        require_test_ready(test, command.user, command.db)
        attempt = AttemptRepository.get_open_exam(
            command.db, user_id=command.user.id, test_id=command.test_id
        )
        if not attempt:
            raise AppError("Сначала начните экзамен", status_code=400)
        composition = get_exam_composition(command.db, attempt, test)
        if command.ticket_id != composition.ticket_id:
            raise AppError("Билет не найден", status_code=404)
        ticket = command.db.get(Ticket, composition.ticket_id)
        if not ticket:
            raise AppError("Билет не найден", status_code=404)
        try:
            ta, remaining = start_ticket_for_exam(
                command.db,
                attempt=attempt,
                ticket=ticket,
                composition=composition,
            )
        except ValueError as e:
            raise AppError(str(e), status_code=408) from e
        questions = load_exam_questions(command.db, composition.question_ids)
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


class SubmitExamTicketAnswersHandler:
    def handle(self, command: SubmitExamTicketAnswersCommand) -> ExamSessionOut:
        test = get_test_or_raise(command.db, command.test_id)
        attempt = AttemptRepository.get_open_exam(
            command.db, user_id=command.user.id, test_id=command.test_id
        )
        if not attempt:
            raise AppError("Нет активной экзаменационной сессии", status_code=400)
        composition = get_exam_composition(command.db, attempt, test)
        if command.ticket_id != composition.ticket_id:
            raise AppError("Билет не найден", status_code=404)
        ticket = command.db.get(Ticket, composition.ticket_id)
        if not ticket:
            raise AppError("Билет не найден", status_code=404)
        try:
            submit_exam_ticket(
                command.db,
                attempt=attempt,
                ticket=ticket,
                composition=composition,
                answers=command.form.answers_map(),
            )
        except ValueError as e:
            raise AppError(str(e), status_code=408) from e
        return _session_out(command.db, test, attempt)


class FinishExamHandler:
    def handle(self, command: FinishExamCommand) -> ExamResultOut:
        test = get_test_or_raise(command.db, command.test_id)
        attempt = AttemptRepository.get_open_exam(
            command.db, user_id=command.user.id, test_id=command.test_id
        )
        if not attempt:
            raise AppError("Нет активной экзаменационной сессии", status_code=400)
        try:
            finish_exam_attempt(command.db, attempt=attempt, test=test)
        except ValueError as e:
            raise AppError(str(e), status_code=400) from e
        return build_exam_result_out(command.db, attempt=attempt, test=test)


class GetExamAttemptResultHandler:
    def handle(self, query: GetExamAttemptResultQuery) -> ExamResultOut:
        test = get_test_or_raise(query.db, query.test_id)
        attempt = AttemptRepository.get_by_id_for_test(
            query.db, query.attempt_id, query.test_id
        )
        if not attempt or attempt.mode != ATTEMPT_MODE_EXAM or attempt.finished_at is None:
            raise AppError("Результат экзамена не найден", status_code=404)
        if attempt.user_id != query.user.id:
            if not can_create_tests(query.user):
                raise AppError("Нет доступа к результату", status_code=403)
            summary = score_attempt(query.db, attempt)
            if not exam_is_passed(summary.percent):
                raise AppError("Нет доступа к результату", status_code=403)
        try:
            return build_exam_result_out(query.db, attempt=attempt, test=test)
        except ValueError as e:
            raise AppError(str(e), status_code=404) from e
