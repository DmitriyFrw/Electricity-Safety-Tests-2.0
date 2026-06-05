from __future__ import annotations

from app.api.mappers import test_edit_out
from app.cache import invalidate_cache
from app.constants import QUESTIONS_PER_TICKET
from app.cqrs.messages.tests import (
    AddTicketCommand,
    DeleteTestCommand,
    DeleteTicketCommand,
    GetTestForEditQuery,
    SaveTicketCommand,
)
from app.models import Attempt, Question, Ticket
from app.policies.test_edit import require_test_edit_access
from app.repositories import TestRepository
from app.schemas import TestEditOut
from app.support.answers import parse_answer_label
from app.support.errors import AppError
from app.support.question_options import clamp_correct_index, clear_unused_options, normalize_option_count
from app.support.rich_text import sanitize_rich_text
from app.support.validation import assert_can_add_ticket


class GetTestForEditHandler:
    def handle(self, query: GetTestForEditQuery) -> TestEditOut:
        require_test_edit_access(query.db, query.test_id, query.user)
        test = TestRepository.get_full_or_raise(query.db, query.test_id)
        return test_edit_out(query.db, test)


class AddTicketHandler:
    def handle(self, command: AddTicketCommand) -> TestEditOut:
        require_test_edit_access(command.db, command.test_id, command.user)
        try:
            assert_can_add_ticket(command.db, command.test_id)
        except ValueError as e:
            raise AppError(str(e), status_code=400) from e
        pos = command.db.query(Ticket).filter(Ticket.test_id == command.test_id).count() + 1
        ticket = Ticket(test_id=command.test_id, position=pos, option_count=4)
        command.db.add(ticket)
        command.db.flush()
        for p in range(1, 2):
            command.db.add(
                Question(
                    ticket_id=ticket.id,
                    position=p,
                    text="",
                    correct_index=0,
                    option_a="",
                    option_b="",
                    option_c="",
                    option_d="",
                )
            )
        command.db.commit()
        invalidate_cache("test_list")
        test = TestRepository.get_full(command.db, command.test_id)
        return test_edit_out(command.db, test)  # type: ignore[arg-type]


class SaveTicketHandler:
    def handle(self, command: SaveTicketCommand) -> TestEditOut:
        require_test_edit_access(command.db, command.test_id, command.user)
        ticket = command.db.get(Ticket, command.ticket_id)
        if not ticket or ticket.test_id != command.test_id:
            raise AppError("Билет не найден", status_code=404)
        ticket.title = command.form.title
        ticket.option_count = normalize_option_count(command.form.option_count)
        saved_positions = {qin.position for qin in command.form.questions}
        for qin in command.form.questions:
            q = (
                command.db.query(Question)
                .filter(
                    Question.ticket_id == command.ticket_id,
                    Question.position == qin.position,
                )
                .one_or_none()
            )
            ci = parse_answer_label(qin.correct)
            if not q:
                q = Question(
                    ticket_id=command.ticket_id,
                    position=qin.position,
                    text="",
                    correct_index=0,
                    option_a="",
                    option_b="",
                    option_c="",
                    option_d="",
                )
                command.db.add(q)
            q.text = sanitize_rich_text(qin.text)
            q.option_a = sanitize_rich_text(qin.option_a)
            q.option_b = sanitize_rich_text(qin.option_b)
            q.option_c = sanitize_rich_text(qin.option_c)
            q.option_d = sanitize_rich_text(qin.option_d)
            q.correct_index = clamp_correct_index(ci if ci is not None else 0, ticket.option_count)
            clear_unused_options(q, ticket.option_count)
        for orphan in (
            command.db.query(Question)
            .filter(Question.ticket_id == command.ticket_id)
            .all()
        ):
            if orphan.position not in saved_positions:
                command.db.delete(orphan)
        command.db.commit()
        invalidate_cache("test_list")
        test = TestRepository.get_full(command.db, command.test_id)
        return test_edit_out(command.db, test)  # type: ignore[arg-type]


class DeleteTicketHandler:
    def handle(self, command: DeleteTicketCommand) -> TestEditOut:
        require_test_edit_access(command.db, command.test_id, command.user)
        ticket = command.db.get(Ticket, command.ticket_id)
        if not ticket or ticket.test_id != command.test_id:
            raise AppError("Билет не найден", status_code=404)
        command.db.delete(ticket)
        command.db.flush()
        remaining = (
            command.db.query(Ticket)
            .filter(Ticket.test_id == command.test_id)
            .order_by(Ticket.position)
            .all()
        )
        for i, t in enumerate(remaining, start=1):
            t.position = i
        command.db.commit()
        invalidate_cache("test_list")
        test = TestRepository.get_full(command.db, command.test_id)
        return test_edit_out(command.db, test)  # type: ignore[arg-type]


class DeleteTestHandler:
    def handle(self, command: DeleteTestCommand) -> None:
        test = require_test_edit_access(command.db, command.test_id, command.user)
        has_attempts = (
            command.db.query(Attempt.id).filter(Attempt.test_id == test.id).limit(1).first()
            is not None
        )
        if has_attempts:
            raise AppError(
                "Нельзя удалить тест: есть попытки прохождения (экзамен или тренировка)",
                status_code=400,
            )
        command.db.delete(test)
        command.db.commit()
        invalidate_cache("test_list")
