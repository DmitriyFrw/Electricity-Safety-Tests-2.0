from __future__ import annotations

from app.api.mappers import exam_paper_out, exam_result_out
from app.cqrs.messages.tests import GetTrainingPaperQuery, SubmitTrainingCommand
from app.schemas import ExamPaperOut, ExamResultOut
from app.services.attempts.scoring import build_question_result_rows, submit_test_attempt_with_answers
from app.services.tests._common import get_test_or_raise, require_test_ready
from app.support.errors import AppError


class GetTrainingPaperHandler:
    def handle(self, query: GetTrainingPaperQuery) -> ExamPaperOut:
        test = get_test_or_raise(query.db, query.test_id)
        require_test_ready(test, query.user, query.db)
        return exam_paper_out(test)


class SubmitTrainingHandler:
    def handle(self, command: SubmitTrainingCommand) -> ExamResultOut:
        test = get_test_or_raise(command.db, command.test_id)
        require_test_ready(test, command.user, command.db)
        try:
            attempt, summary, ticket_rows = submit_test_attempt_with_answers(
                command.db,
                user_id=command.user.id,
                test=test,
                answers=command.form.answers_map(),
            )
        except ValueError as e:
            raise AppError(str(e), status_code=400) from e
        command.db.refresh(attempt, attribute_names=["user_answers"])
        return exam_result_out(
            test,
            summary,
            ticket_rows,
            attempt_id=attempt.id,
            protocol_signed=False,
            question_rows=build_question_result_rows(test, attempt.user_answers),
        )
