from __future__ import annotations

from sqlalchemy.orm import Session

from app.cqrs.bus import dispatch_command, dispatch_query
from app.cqrs.messages import (
    AddTicketCommand,
    CreateTestCommand,
    DeleteTicketCommand,
    FinishExamCommand,
    GetExamSessionQuery,
    GetSignedProtocolPdfQuery,
    GetSignedProtocolQuery,
    GetTestForEditQuery,
    GetTrainingPaperQuery,
    ListTestsQuery,
    OpenExamTicketCommand,
    SaveTicketCommand,
    SignProtocolCommand,
    StartExamSessionCommand,
    SubmitExamTicketAnswersCommand,
    SubmitTrainingCommand,
)
from app.form_requests.tests import SubmitExamRequest, TestCreateRequest, TicketSaveRequest
from app.models import User
from app.schemas import (
    ExamPaperOut,
    ExamResultOut,
    ExamSessionOut,
    ExamTicketPaperOut,
    SignedProtocolOut,
    TestCreateOut,
    TestEditOut,
    TestListOut,
)


class TestService:
    """Фасад CQRS: делегирует в CommandBus / QueryBus."""

    @staticmethod
    def list_tests(db: Session, user: User) -> TestListOut:
        return dispatch_query(ListTestsQuery(db=db, user=user), TestListOut)

    @staticmethod
    def create_test(db: Session, user: User, form: TestCreateRequest) -> TestCreateOut:
        return dispatch_command(CreateTestCommand(db=db, user=user, form=form), TestCreateOut)

    @staticmethod
    def get_test_for_edit(db: Session, test_id: int, user: User) -> TestEditOut:
        return dispatch_query(GetTestForEditQuery(db=db, test_id=test_id, user=user), TestEditOut)

    @staticmethod
    def add_ticket(db: Session, test_id: int, user: User) -> TestEditOut:
        return dispatch_command(AddTicketCommand(db=db, test_id=test_id, user=user), TestEditOut)

    @staticmethod
    def save_ticket(
        db: Session, test_id: int, ticket_id: int, user: User, form: TicketSaveRequest
    ) -> TestEditOut:
        return dispatch_command(
            SaveTicketCommand(db=db, test_id=test_id, ticket_id=ticket_id, user=user, form=form),
            TestEditOut,
        )

    @staticmethod
    def delete_ticket(db: Session, test_id: int, ticket_id: int, user: User) -> TestEditOut:
        return dispatch_command(
            DeleteTicketCommand(db=db, test_id=test_id, ticket_id=ticket_id, user=user), TestEditOut
        )

    @staticmethod
    def get_training_paper(db: Session, test_id: int, user: User) -> ExamPaperOut:
        return dispatch_query(
            GetTrainingPaperQuery(db=db, test_id=test_id, user=user), ExamPaperOut
        )

    @staticmethod
    def submit_training(
        db: Session, test_id: int, user: User, form: SubmitExamRequest
    ) -> ExamResultOut:
        return dispatch_command(
            SubmitTrainingCommand(db=db, test_id=test_id, user=user, form=form), ExamResultOut
        )

    @staticmethod
    def start_exam_session(db: Session, test_id: int, user: User) -> ExamSessionOut:
        return dispatch_command(
            StartExamSessionCommand(db=db, test_id=test_id, user=user), ExamSessionOut
        )

    @staticmethod
    def get_exam_session(db: Session, test_id: int, user: User) -> ExamSessionOut:
        return dispatch_query(GetExamSessionQuery(db=db, test_id=test_id, user=user), ExamSessionOut)

    @staticmethod
    def get_exam_ticket(
        db: Session, test_id: int, ticket_id: int, user: User
    ) -> ExamTicketPaperOut:
        return dispatch_command(
            OpenExamTicketCommand(db=db, test_id=test_id, ticket_id=ticket_id, user=user),
            ExamTicketPaperOut,
        )

    @staticmethod
    def submit_exam_ticket_answers(
        db: Session, test_id: int, ticket_id: int, user: User, form: SubmitExamRequest
    ) -> ExamSessionOut:
        return dispatch_command(
            SubmitExamTicketAnswersCommand(
                db=db, test_id=test_id, ticket_id=ticket_id, user=user, form=form
            ),
            ExamSessionOut,
        )

    @staticmethod
    def finish_exam(db: Session, test_id: int, user: User) -> ExamResultOut:
        return dispatch_command(FinishExamCommand(db=db, test_id=test_id, user=user), ExamResultOut)

    @staticmethod
    def sign_protocol(db: Session, test_id: int, attempt_id: int, signer: User) -> SignedProtocolOut:
        return dispatch_command(
            SignProtocolCommand(db=db, test_id=test_id, attempt_id=attempt_id, signer=signer),
            SignedProtocolOut,
        )

    @staticmethod
    def get_signed_protocol(
        db: Session, test_id: int, attempt_id: int, requester: User
    ) -> SignedProtocolOut:
        return dispatch_query(
            GetSignedProtocolQuery(
                db=db, test_id=test_id, attempt_id=attempt_id, requester=requester
            ),
            SignedProtocolOut,
        )

    @staticmethod
    def get_signed_protocol_pdf(
        db: Session, test_id: int, attempt_id: int, requester: User
    ) -> bytes:
        return dispatch_query(
            GetSignedProtocolPdfQuery(
                db=db, test_id=test_id, attempt_id=attempt_id, requester=requester
            ),
            bytes,
        )
