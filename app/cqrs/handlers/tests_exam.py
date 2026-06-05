from __future__ import annotations

from sqlalchemy.orm import Session

from app.api.mappers import exam_result_out, exam_session_out, exam_ticket_paper_out
from app.cqrs.messages.tests import (
    FinishExamCommand,
    GetExamSessionQuery,
    OpenExamTicketCommand,
    StartExamSessionCommand,
    SubmitExamTicketAnswersCommand,
)
from app.models import Attempt, Test, Ticket
from app.repositories import AttemptRepository, ProtocolRepository
from app.schemas import ExamResultOut, ExamSessionOut, ExamTicketPaperOut
from app.services.exams.session import (
    completed_ticket_ids,
    create_exam_attempt,
    finish_exam_attempt,
    next_ticket,
    start_ticket_for_exam,
    submit_exam_ticket,
    ticket_deadline,
)
from app.services.tests._common import get_test_or_raise, require_test_ready
from app.support.errors import AppError


def _session_out(db: Session, test: Test, attempt: Attempt) -> ExamSessionOut:
    done = set(completed_ticket_ids(db, attempt))
    nxt = next_ticket(test, done)
    return exam_session_out(
        attempt_id=attempt.id,
        test=test,
        completed_ticket_ids=sorted(done),
        next_ticket_id=nxt.id if nxt else None,
    )


class StartExamSessionHandler:
    def handle(self, command: StartExamSessionCommand) -> ExamSessionOut:
        test = get_test_or_raise(command.db, command.test_id)
        require_test_ready(test, command.user, command.db)
        attempt = create_exam_attempt(command.db, user_id=command.user.id, test_id=test.id)
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
        ticket = command.db.get(Ticket, command.ticket_id)
        if not ticket or ticket.test_id != command.test_id:
            raise AppError("Билет не найден", status_code=404)
        try:
            ta, remaining = start_ticket_for_exam(
                command.db, attempt=attempt, ticket=ticket, test=test
            )
        except ValueError as e:
            raise AppError(str(e), status_code=408) from e
        tickets_sorted = sorted(test.tickets, key=lambda t: t.position)
        ticket_index = next(
            i for i, t in enumerate(tickets_sorted, start=1) if t.id == ticket.id
        )
        return exam_ticket_paper_out(
            test=test,
            attempt_id=attempt.id,
            ticket=ticket,
            ticket_index=ticket_index,
            seconds_remaining=remaining,
            deadline_at=ticket_deadline(ta.started_at),
        )


class SubmitExamTicketAnswersHandler:
    def handle(self, command: SubmitExamTicketAnswersCommand) -> ExamSessionOut:
        test = get_test_or_raise(command.db, command.test_id)
        attempt = AttemptRepository.get_open_exam(
            command.db, user_id=command.user.id, test_id=command.test_id
        )
        if not attempt:
            raise AppError("Нет активной экзаменационной сессии", status_code=400)
        ticket = command.db.get(Ticket, command.ticket_id)
        if not ticket or ticket.test_id != command.test_id:
            raise AppError("Билет не найден", status_code=404)
        try:
            submit_exam_ticket(
                command.db,
                attempt=attempt,
                ticket=ticket,
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
            summary, ticket_rows = finish_exam_attempt(
                command.db, attempt=attempt, test=test
            )
        except ValueError as e:
            raise AppError(str(e), status_code=400) from e
        protocol = ProtocolRepository.get_by_attempt_id(command.db, attempt.id)
        return exam_result_out(
            test,
            summary,
            ticket_rows,
            attempt_id=attempt.id,
            protocol_signed=protocol is not None,
        )
