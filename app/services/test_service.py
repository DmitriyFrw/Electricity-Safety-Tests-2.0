from __future__ import annotations

from sqlalchemy.orm import Session

from app.answer_labels import parse_answer_label
from app.api_serializers import (
    exam_paper_out,
    exam_result_out,
    exam_session_out,
    exam_ticket_paper_out,
    test_edit_out,
    test_list_out,
)
from app.attempt_service import submit_test_attempt_with_answers
from app.constants import MIN_PASS_PERCENT, QUESTIONS_PER_TICKET
from app.deps import require_test_edit_access
from app.exceptions import AppError
from app.exam_service import (
    completed_ticket_ids,
    create_exam_attempt,
    finish_exam_attempt,
    get_open_exam_attempt,
    next_ticket,
    start_ticket_for_exam,
    submit_exam_ticket,
    ticket_deadline,
)
from app.form_requests.tests import SubmitExamRequest, TestCreateRequest, TicketSaveRequest
from app.models import Attempt, Question, SignedProtocol, Test, Ticket, User
from app.policies import AccessPolicy
from app.pdf_service import build_signed_protocol_pdf
from app.repositories import TestRepository
from app.schemas import (
    ExamPaperOut,
    ExamResultOut,
    ExamSessionOut,
    ExamTicketPaperOut,
    TestCreateOut,
    TestEditOut,
    TestListOut,
    SignedProtocolOut,
)
from app.validation import assert_can_add_ticket, test_is_ready_loaded, test_is_ready_to_take


class TestService:
    @staticmethod
    def list_tests(db: Session, user: User) -> TestListOut:
        tests = TestRepository.list_all(db)
        return test_list_out(db, tests, user)

    @staticmethod
    def create_test(db: Session, user: User, form: TestCreateRequest) -> TestCreateOut:
        test = Test(
            author_id=user.id,
            title=form.title,
            description=form.description,
        )
        db.add(test)
        db.commit()
        db.refresh(test)
        return TestCreateOut(id=test.id, title=test.title)

    @staticmethod
    def get_test_for_edit(db: Session, test_id: int, user: User) -> TestEditOut:
        require_test_edit_access(db, test_id, user)
        test = TestRepository.get_full(db, test_id)
        if not test:
            raise AppError("Тест не найден", status_code=404)
        return test_edit_out(db, test)

    @staticmethod
    def _require_ready(test: Test, user: User, db: Session) -> None:
        ready = test_is_ready_loaded(test) if test.tickets else test_is_ready_to_take(db, test)
        if not ready:
            if user.id == test.author_id:
                raise AppError("Тест ещё не заполнен полностью", status_code=400)
            raise AppError("Тест недоступен для сдачи", status_code=400)

    @staticmethod
    def get_training_paper(db: Session, test_id: int, user: User) -> ExamPaperOut:
        test = TestRepository.get_full(db, test_id)
        if not test:
            raise AppError("Тест не найден", status_code=404)
        TestService._require_ready(test, user, db)
        return exam_paper_out(test)

    @staticmethod
    def submit_training(
        db: Session, test_id: int, user: User, form: SubmitExamRequest
    ) -> ExamResultOut:
        test = TestRepository.get_full(db, test_id)
        if not test:
            raise AppError("Тест не найден", status_code=404)
        TestService._require_ready(test, user, db)
        _attempt, summary, ticket_rows = submit_test_attempt_with_answers(
            db,
            user_id=user.id,
            test=test,
            answers=form.answers_map(),
        )
        return exam_result_out(
            test, summary, ticket_rows, attempt_id=_attempt.id, protocol_signed=False
        )

    @staticmethod
    def start_exam_session(db: Session, test_id: int, user: User) -> ExamSessionOut:
        test = TestRepository.get_full(db, test_id)
        if not test:
            raise AppError("Тест не найден", status_code=404)
        TestService._require_ready(test, user, db)
        attempt = create_exam_attempt(db, user_id=user.id, test_id=test.id)
        return TestService._session_out(db, test, attempt)

    @staticmethod
    def get_exam_session(db: Session, test_id: int, user: User) -> ExamSessionOut:
        test = TestRepository.get_full(db, test_id)
        if not test:
            raise AppError("Тест не найден", status_code=404)
        attempt = get_open_exam_attempt(db, user_id=user.id, test_id=test_id)
        if not attempt:
            raise AppError("Нет активной экзаменационной сессии", status_code=404)
        return TestService._session_out(db, test, attempt)

    @staticmethod
    def _session_out(db: Session, test: Test, attempt) -> ExamSessionOut:
        done = set(completed_ticket_ids(db, attempt))
        nxt = next_ticket(test, done)
        return exam_session_out(
            attempt_id=attempt.id,
            test=test,
            completed_ticket_ids=sorted(done),
            next_ticket_id=nxt.id if nxt else None,
        )

    @staticmethod
    def get_exam_ticket(
        db: Session, test_id: int, ticket_id: int, user: User
    ) -> ExamTicketPaperOut:
        test = TestRepository.get_full(db, test_id)
        if not test:
            raise AppError("Тест не найден", status_code=404)
        TestService._require_ready(test, user, db)
        attempt = get_open_exam_attempt(db, user_id=user.id, test_id=test_id)
        if not attempt:
            raise AppError("Сначала начните экзамен", status_code=400)
        ticket = db.get(Ticket, ticket_id)
        if not ticket or ticket.test_id != test_id:
            raise AppError("Билет не найден", status_code=404)
        try:
            ta, remaining = start_ticket_for_exam(
                db, attempt=attempt, ticket=ticket, test=test
            )
        except ValueError as e:
            raise AppError(str(e), status_code=408) from e
        tickets_sorted = sorted(test.tickets, key=lambda t: t.position)
        ticket_index = next(i for i, t in enumerate(tickets_sorted, start=1) if t.id == ticket.id)
        return exam_ticket_paper_out(
            test=test,
            attempt_id=attempt.id,
            ticket=ticket,
            ticket_index=ticket_index,
            seconds_remaining=remaining,
            deadline_at=ticket_deadline(ta.started_at),
        )

    @staticmethod
    def submit_exam_ticket_answers(
        db: Session, test_id: int, ticket_id: int, user: User, form: SubmitExamRequest
    ) -> ExamSessionOut:
        test = TestRepository.get_full(db, test_id)
        if not test:
            raise AppError("Тест не найден", status_code=404)
        attempt = get_open_exam_attempt(db, user_id=user.id, test_id=test_id)
        if not attempt:
            raise AppError("Нет активной экзаменационной сессии", status_code=400)
        ticket = db.get(Ticket, ticket_id)
        if not ticket or ticket.test_id != test_id:
            raise AppError("Билет не найден", status_code=404)
        try:
            submit_exam_ticket(
                db, attempt=attempt, ticket=ticket, answers=form.answers_map()
            )
        except ValueError as e:
            raise AppError(str(e), status_code=408) from e
        return TestService._session_out(db, test, attempt)

    @staticmethod
    def finish_exam(db: Session, test_id: int, user: User) -> ExamResultOut:
        test = TestRepository.get_full(db, test_id)
        if not test:
            raise AppError("Тест не найден", status_code=404)
        attempt = get_open_exam_attempt(db, user_id=user.id, test_id=test_id)
        if not attempt:
            raise AppError("Нет активной экзаменационной сессии", status_code=400)
        try:
            summary, ticket_rows = finish_exam_attempt(db, attempt=attempt, test=test)
        except ValueError as e:
            raise AppError(str(e), status_code=400) from e
        protocol = (
            db.query(SignedProtocol).filter(SignedProtocol.attempt_id == attempt.id).one_or_none()
        )
        return exam_result_out(
            test,
            summary,
            ticket_rows,
            attempt_id=attempt.id,
            protocol_signed=protocol is not None,
        )

    @staticmethod
    def sign_protocol(
        db: Session, test_id: int, attempt_id: int, signer: User
    ) -> SignedProtocolOut:
        if not AccessPolicy.can_create_tests(signer):
            raise AppError("Подписывать протокол может только admin или Еж", status_code=403)
        attempt = (
            db.query(Attempt)
            .filter(Attempt.id == attempt_id, Attempt.test_id == test_id)
            .one_or_none()
        )
        if not attempt:
            raise AppError("Попытка не найдена", status_code=404)
        if attempt.finished_at is None:
            raise AppError("Экзамен ещё не завершён", status_code=400)

        existing = (
            db.query(SignedProtocol).filter(SignedProtocol.attempt_id == attempt_id).one_or_none()
        )
        if existing:
            return TestService._protocol_out(existing)

        examinee = db.get(User, attempt.user_id)
        test = db.get(Test, attempt.test_id)
        if not examinee or not test:
            raise AppError("Недостаточно данных для подписания протокола", status_code=400)
        if not examinee.full_name or not examinee.birth_date or not examinee.job_title:
            raise AppError(
                "У пользователя Кот не заполнены ФИО, дата рождения или должность в профиле",
                status_code=400,
            )

        total = len(attempt.user_answers)
        correct = sum(
            1
            for ua in attempt.user_answers
            if ua.selected_index is not None
            and ua.question is not None
            and ua.selected_index == ua.question.correct_index
        )
        percent = int(round((correct / total) * 100)) if total else 0
        if percent < MIN_PASS_PERCENT:
            raise AppError(
                "Протокол можно подписать только после успешной сдачи экзамена",
                status_code=400,
            )

        protocol = SignedProtocol(
            attempt_id=attempt.id,
            signer_id=signer.id,
            examinee_id=examinee.id,
            examinee_full_name=examinee.full_name,
            examinee_birth_date=examinee.birth_date,
            examinee_job_title=examinee.job_title,
            test_title=test.title,
            result_percent=percent,
        )
        db.add(protocol)
        db.commit()
        db.refresh(protocol)
        return TestService._protocol_out(protocol)

    @staticmethod
    def get_signed_protocol(db: Session, test_id: int, attempt_id: int) -> SignedProtocolOut:
        protocol = (
            db.query(SignedProtocol)
            .filter(SignedProtocol.attempt_id == attempt_id)
            .one_or_none()
        )
        if not protocol:
            raise AppError("Протокол ещё не подписан", status_code=404)
        if protocol.attempt is None or protocol.attempt.test_id != test_id:
            raise AppError("Протокол не найден", status_code=404)
        return TestService._protocol_out(protocol)

    @staticmethod
    def get_signed_protocol_pdf(db: Session, test_id: int, attempt_id: int) -> bytes:
        protocol = (
            db.query(SignedProtocol)
            .filter(SignedProtocol.attempt_id == attempt_id)
            .one_or_none()
        )
        if not protocol:
            raise AppError("Протокол ещё не подписан", status_code=404)
        if protocol.attempt is None or protocol.attempt.test_id != test_id:
            raise AppError("Протокол не найден", status_code=404)
        return build_signed_protocol_pdf(protocol)

    @staticmethod
    def _protocol_out(protocol: SignedProtocol) -> SignedProtocolOut:
        signer_username = protocol.signer.username if protocol.signer else ""
        return SignedProtocolOut(
            attempt_id=protocol.attempt_id,
            test_id=protocol.attempt.test_id if protocol.attempt else 0,
            signer_id=protocol.signer_id,
            signer_username=signer_username,
            examinee_id=protocol.examinee_id,
            examinee_full_name=protocol.examinee_full_name,
            examinee_birth_date=protocol.examinee_birth_date,
            examinee_job_title=protocol.examinee_job_title,
            test_title=protocol.test_title,
            result_percent=protocol.result_percent,
            signed_at=protocol.signed_at,
        )

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
        for p in range(1, QUESTIONS_PER_TICKET + 1):
            db.add(
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
        db.commit()
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
            ci = parse_answer_label(qin.correct)
            q.text = qin.text.strip()
            q.option_a = qin.option_a.strip()
            q.option_b = qin.option_b.strip()
            q.option_c = qin.option_c.strip()
            q.option_d = qin.option_d.strip()
            q.correct_index = ci if ci is not None else 0
        db.commit()
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
        test = TestRepository.get_full(db, test_id)
        return test_edit_out(db, test)  # type: ignore[arg-type]
