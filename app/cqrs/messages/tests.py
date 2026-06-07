from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.cqrs.base import Command, Query
from app.form_requests.tests import SubmitExamRequest, TestCreateRequest, TicketSaveRequest
from app.schemas import TestSettingsIn
from app.models import User


@dataclass(frozen=True, slots=True)
class ListTestsQuery(Query):
    db: Session
    user: User


@dataclass(frozen=True, slots=True)
class CreateTestCommand(Command):
    db: Session
    user: User
    form: TestCreateRequest


@dataclass(frozen=True, slots=True)
class GetTestForEditQuery(Query):
    db: Session
    test_id: int
    user: User


@dataclass(frozen=True, slots=True)
class AddTicketCommand(Command):
    db: Session
    test_id: int
    user: User


@dataclass(frozen=True, slots=True)
class SaveTicketCommand(Command):
    db: Session
    test_id: int
    ticket_id: int
    user: User
    form: TicketSaveRequest


@dataclass(frozen=True, slots=True)
class DeleteTicketCommand(Command):
    db: Session
    test_id: int
    ticket_id: int
    user: User


@dataclass(frozen=True, slots=True)
class DeleteTestCommand(Command):
    db: Session
    test_id: int
    user: User


@dataclass(frozen=True, slots=True)
class UpdateTestSettingsCommand(Command):
    db: Session
    test_id: int
    user: User
    form: TestSettingsIn


@dataclass(frozen=True, slots=True)
class PublishTestCommand(Command):
    db: Session
    test_id: int
    user: User


@dataclass(frozen=True, slots=True)
class GetTrainingPaperQuery(Query):
    db: Session
    test_id: int
    user: User


@dataclass(frozen=True, slots=True)
class SubmitTrainingCommand(Command):
    db: Session
    test_id: int
    user: User
    form: SubmitExamRequest


@dataclass(frozen=True, slots=True)
class StartExamSessionCommand(Command):
    db: Session
    test_id: int
    user: User


@dataclass(frozen=True, slots=True)
class GetExamSessionQuery(Query):
    db: Session
    test_id: int
    user: User


@dataclass(frozen=True, slots=True)
class OpenExamTicketCommand(Command):
    """Открыть билет экзамена (создаёт/обновляет TicketAttempt)."""

    db: Session
    test_id: int
    ticket_id: int
    user: User


@dataclass(frozen=True, slots=True)
class SubmitExamTicketAnswersCommand(Command):
    db: Session
    test_id: int
    ticket_id: int
    user: User
    form: SubmitExamRequest


@dataclass(frozen=True, slots=True)
class FinishExamCommand(Command):
    db: Session
    test_id: int
    user: User


@dataclass(frozen=True, slots=True)
class GetExamAttemptResultQuery(Query):
    db: Session
    test_id: int
    attempt_id: int
    user: User


@dataclass(frozen=True, slots=True)
class SignProtocolCommand(Command):
    db: Session
    test_id: int
    attempt_id: int
    signer: User


@dataclass(frozen=True, slots=True)
class GetSignedProtocolQuery(Query):
    db: Session
    test_id: int
    attempt_id: int
    requester: User


@dataclass(frozen=True, slots=True)
class GetSignedProtocolPdfQuery(Query):
    db: Session
    test_id: int
    attempt_id: int
    requester: User


@dataclass(frozen=True, slots=True)
class GetAttemptProtocolFormPdfQuery(Query):
    db: Session
    test_id: int
    attempt_id: int
    requester: User


@dataclass(frozen=True, slots=True)
class GetAttemptProtocolDraftPdfQuery(Query):
    db: Session
    test_id: int
    attempt_id: int
    requester: User
