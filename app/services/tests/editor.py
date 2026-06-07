from __future__ import annotations

from sqlalchemy.orm import Session

from app.policies.test_edit import require_test_edit_access
from app.api.mappers import test_edit_out
from app.cache import invalidate_cache
from app.constants import QUESTIONS_PER_TICKET
from app.form_requests.tests import TicketSaveRequest
from app.models import Question, Ticket, User
from app.repositories import TestRepository
from app.support.answers import encode_correct_indexes, parse_answer_labels
from app.support.errors import AppError
from app.support.validation import assert_can_add_ticket
from app.schemas import TestEditOut


class TestEditorService:
    @staticmethod
    def get_test_for_edit(db: Session, test_id: int, user: User) -> TestEditOut:
        require_test_edit_access(db, test_id, user)
        test = TestRepository.get_full_or_raise(db, test_id)
        return test_edit_out(db, test)

    @staticmethod
    def add_ticket(db: Session, test_id: int, user: User) -> TestEditOut:
        require_test_edit_access(db, test_id, user)
        try:
            assert_can_add_ticket(db, test_id)
        except ValueError as e:
            raise AppError(str(e), status_code=400) from e
        pos = db.query(Ticket).filter(Ticket.test_id == test_id).count() + 1
        ticket = Ticket(test_id=test_id, position=pos)
        db.add(ticket)
        db.flush()
        for p in range(1, 2):
            db.add(
                Question(
                    ticket_id=ticket.id,
                    position=p,
                    text="",
                    correct_index=0,
                    correct_indexes="0",
                    option_a="",
                    option_b="",
                    option_c="",
                    option_d="",
                )
            )
        db.commit()
        invalidate_cache("test_list")
        test = TestRepository.get_full(db, test_id)
        return test_edit_out(db, test)  # type: ignore[arg-type]

    @staticmethod
    def save_ticket(
        db: Session,
        test_id: int,
        ticket_id: int,
        user: User,
        form: TicketSaveRequest,
    ) -> TestEditOut:
        require_test_edit_access(db, test_id, user)
        ticket = db.get(Ticket, ticket_id)
        if not ticket or ticket.test_id != test_id:
            raise AppError("Билет не найден", status_code=404)
        for qin in form.questions:
            q = (
                db.query(Question)
                .filter(Question.ticket_id == ticket_id, Question.position == qin.position)
                .one_or_none()
            )
            if not q:
                continue
            indices = parse_answer_labels(qin.correct, option_count=form.option_count)
            q.text = qin.text.strip()
            q.option_a = qin.option_a.strip()
            q.option_b = qin.option_b.strip()
            q.option_c = qin.option_c.strip()
            q.option_d = qin.option_d.strip()
            q.correct_indexes = encode_correct_indexes(indices)
            q.correct_index = indices[0]
        db.commit()
        invalidate_cache("test_list")
        test = TestRepository.get_full(db, test_id)
        return test_edit_out(db, test)  # type: ignore[arg-type]

    @staticmethod
    def delete_ticket(db: Session, test_id: int, ticket_id: int, user: User) -> TestEditOut:
        require_test_edit_access(db, test_id, user)
        ticket = db.get(Ticket, ticket_id)
        if not ticket or ticket.test_id != test_id:
            raise AppError("Билет не найден", status_code=404)
        db.delete(ticket)
        db.flush()
        remaining = (
            db.query(Ticket).filter(Ticket.test_id == test_id).order_by(Ticket.position).all()
        )
        for i, t in enumerate(remaining, start=1):
            t.position = i
        db.commit()
        invalidate_cache("test_list")
        test = TestRepository.get_full(db, test_id)
        return test_edit_out(db, test)  # type: ignore[arg-type]
