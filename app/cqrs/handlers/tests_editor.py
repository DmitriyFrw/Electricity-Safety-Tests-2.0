from __future__ import annotations

from app.api.mappers import test_edit_out
from app.cache import invalidate_cache
from app.constants import MIN_OPTION_COUNT, QUESTIONS_PER_TICKET
from app.cqrs.messages.tests import (
    AddTicketCommand,
    DeleteTestCommand,
    DeleteTicketCommand,
    GetTestForEditQuery,
    PublishTestCommand,
    SaveTicketCommand,
    UpdateTestSettingsCommand,
)
from app.models import Attempt, Question, Ticket
from app.policies.test_edit import require_test_edit_access
from app.repositories import TestRepository
from app.schemas import TestEditOut
from app.support.answers import encode_correct_indexes, parse_answer_labels
from app.support.errors import AppError
from app.support.question_options import clamp_correct_index, clear_unused_options, normalize_option_count
from app.support.rich_text import sanitize_rich_text
from app.support.validation import assert_can_add_ticket, test_is_ready_to_take


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
                    correct_indexes="0",
                    option_count=4,
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
        max_option_count = MIN_OPTION_COUNT
        saved_positions = {qin.position for qin in command.form.questions}
        for qin in command.form.questions:
            q_count = normalize_option_count(qin.option_count)
            max_option_count = max(max_option_count, q_count)
            q = (
                command.db.query(Question)
                .filter(
                    Question.ticket_id == command.ticket_id,
                    Question.position == qin.position,
                )
                .one_or_none()
            )
            indices = parse_answer_labels(qin.correct, option_count=q_count)
            if not q:
                q = Question(
                    ticket_id=command.ticket_id,
                    position=qin.position,
                    text="",
                    correct_index=0,
                    correct_indexes="0",
                    option_count=q_count,
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
            q.option_count = q_count
            q.correct_indexes = encode_correct_indexes(indices)
            q.correct_index = clamp_correct_index(indices[0], q_count)
            clear_unused_options(q, q_count)
        ticket.option_count = max_option_count
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


class UpdateTestSettingsHandler:
    def handle(self, command: UpdateTestSettingsCommand) -> TestEditOut:
        test = require_test_edit_access(command.db, command.test_id, command.user)
        test.random_ticket_order = command.form.random_ticket_order
        command.db.commit()
        invalidate_cache("test_list")
        full = TestRepository.get_full_or_raise(command.db, command.test_id)
        return test_edit_out(command.db, full)


class PublishTestHandler:
    def handle(self, command: PublishTestCommand) -> TestEditOut:
        test = require_test_edit_access(command.db, command.test_id, command.user)
        if test.published:
            raise AppError("Тест уже опубликован", status_code=400)
        if not test_is_ready_to_take(command.db, test):
            raise AppError(
                "Добавьте хотя бы один билет с 10 вопросами и вариантами ответов",
                status_code=400,
            )
        test.published = True
        command.db.commit()
        invalidate_cache("test_list")
        full = TestRepository.get_full_or_raise(command.db, command.test_id)
        return test_edit_out(command.db, full)
