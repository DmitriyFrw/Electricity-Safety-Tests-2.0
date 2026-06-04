from __future__ import annotations

from sqlalchemy.orm import Session

from app.api.mappers import exam_paper_out, exam_result_out
from app.form_requests.tests import SubmitExamRequest
from app.models import User
from app.services.attempts.scoring import submit_test_attempt_with_answers
from app.services.tests._common import get_test_or_raise, require_test_ready
from app.schemas import ExamPaperOut, ExamResultOut


class TestTrainingService:
    @staticmethod
    def get_training_paper(db: Session, test_id: int, user: User) -> ExamPaperOut:
        test = get_test_or_raise(db, test_id)
        require_test_ready(test, user, db)
        return exam_paper_out(test)

    @staticmethod
    def submit_training(
        db: Session, test_id: int, user: User, form: SubmitExamRequest
    ) -> ExamResultOut:
        test = get_test_or_raise(db, test_id)
        require_test_ready(test, user, db)
        attempt, summary, ticket_rows = submit_test_attempt_with_answers(
            db,
            user_id=user.id,
            test=test,
            answers=form.answers_map(),
        )
        return exam_result_out(
            test, summary, ticket_rows, attempt_id=attempt.id, protocol_signed=False
        )
