from __future__ import annotations

from sqlalchemy.orm import Session

from app.api.mappers import exam_paper_out, exam_result_out
from app.constants import ATTEMPT_MODE_TRAINING
from app.cqrs.messages.tests import (
    GetTrainingAttemptResultQuery,
    GetTrainingPaperQuery,
    SubmitTrainingCommand,
)
from app.models import Attempt, Test
from app.repositories import AttemptRepository
from app.services.training_paper import ensure_training_paper_attempt
from app.support.question_option_order import parse_option_orders, remap_answers_map
from app.support.exam_ticket_order import parse_ticket_id_order, tickets_by_id_order
from app.support.validation import complete_tickets_sorted
from app.schemas import ExamPaperOut, ExamResultOut
from app.services.attempts.scoring import (
    build_question_result_rows,
    build_training_ticket_rows,
    finish_training_attempt_with_answers,
    score_attempt,
    submit_test_attempt_with_answers,
)
from app.support.test_access import get_test_or_raise, require_test_ready
from app.support.errors import AppError


def build_training_result_out(db: Session, *, attempt: Attempt, test: Test) -> ExamResultOut:
    db.refresh(attempt, attribute_names=["user_answers"])
    summary = score_attempt(db, attempt)
    ticket_rows = build_training_ticket_rows(test, attempt.user_answers)
    return exam_result_out(
        test,
        summary,
        ticket_rows,
        attempt_id=attempt.id,
        protocol_signed=False,
        question_rows=build_question_result_rows(test, attempt.user_answers),
        passed_exam=False,
    )


class GetTrainingPaperHandler:
    def handle(self, query: GetTrainingPaperQuery) -> ExamPaperOut:
        test = get_test_or_raise(query.db, query.test_id)
        require_test_ready(test, query.user, query.db)
        _attempt, orders, ticket_ids = ensure_training_paper_attempt(
            query.db, user_id=query.user.id, test=test
        )
        return exam_paper_out(
            test, option_orders=orders or None, ticket_ids=ticket_ids or None
        )


class SubmitTrainingHandler:
    def handle(self, command: SubmitTrainingCommand) -> ExamResultOut:
        test = get_test_or_raise(command.db, command.test_id)
        require_test_ready(test, command.user, command.db)
        answers = command.form.answers_map()
        open_attempt = AttemptRepository.get_open_training(
            command.db, user_id=command.user.id, test_id=command.test_id
        )
        if open_attempt:
            orders = parse_option_orders(open_attempt.question_option_orders) or {}
            if orders:
                ticket_ids = parse_ticket_id_order(open_attempt.exam_ticket_order)
                ordered_tickets = (
                    tickets_by_id_order(test, ticket_ids)
                    if ticket_ids
                    else complete_tickets_sorted(test)
                )
                questions = {
                    q.id: q for ticket in ordered_tickets for q in ticket.questions
                }
                answers = remap_answers_map(answers, orders, questions)
        try:
            if open_attempt:
                attempt, _, _ = finish_training_attempt_with_answers(
                    command.db,
                    attempt=open_attempt,
                    test=test,
                    answers=answers,
                )
            else:
                attempt, _, _ = submit_test_attempt_with_answers(
                    command.db,
                    user_id=command.user.id,
                    test=test,
                    answers=answers,
                )
        except ValueError as e:
            raise AppError(str(e), status_code=400) from e
        return build_training_result_out(command.db, attempt=attempt, test=test)


class GetTrainingAttemptResultHandler:
    def handle(self, query: GetTrainingAttemptResultQuery) -> ExamResultOut:
        test = get_test_or_raise(query.db, query.test_id)
        attempt = AttemptRepository.get_by_id_for_test(
            query.db, query.attempt_id, query.test_id
        )
        if (
            not attempt
            or attempt.mode != ATTEMPT_MODE_TRAINING
            or attempt.finished_at is None
        ):
            raise AppError("Результат тренировки не найден", status_code=404)
        if attempt.user_id != query.user.id:
            raise AppError("Нет доступа к результату", status_code=403)
        return build_training_result_out(query.db, attempt=attempt, test=test)
