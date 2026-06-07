from __future__ import annotations

from sqlalchemy.orm import Session

from app.support.grading import exam_is_passed
from app.cqrs.messages.tests import (
    GetAttemptProtocolDraftPdfQuery,
    GetAttemptProtocolFormPdfQuery,
    GetSignedProtocolPdfQuery,
    GetSignedProtocolQuery,
    SignProtocolCommand,
)
from app.models import Attempt, SignedProtocol, User
from app.policies import AccessPolicy
from app.repositories import AttemptRepository, ProtocolRepository, TestRepository, UserRepository
from app.schemas import SignedProtocolOut
from app.services.attempts.scoring import score_attempt
from app.services.pdf.protocol import (
    build_examinee_protocol_form_pdf,
    build_protocol_pdf,
    build_signed_protocol_pdf,
)
from app.support.errors import AppError
from app.support.profile import require_profile_complete


def _require_protocol_exporter(requester: User) -> None:
    if not AccessPolicy.can_create_tests(requester):
        raise AppError(
            "Выгружать протокол могут только admin или Еж",
            status_code=403,
        )


def _examinee_for_attempt(
    db: Session, test_id: int, attempt_id: int
) -> tuple[Attempt, User]:
    attempt = AttemptRepository.get_by_id_for_test(db, attempt_id, test_id)
    if not attempt:
        raise AppError("Попытка не найдена", status_code=404)
    examinee = UserRepository.get_by_id(db, attempt.user_id)
    if not examinee:
        raise AppError("Экзаменуемый не найден", status_code=404)
    require_profile_complete(examinee)
    return attempt, examinee


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


def _require_signed_protocol_reader(protocol: SignedProtocol, requester: User) -> None:
    """Экзаменуемый, подписант или admin/ezh."""
    if requester.id == protocol.examinee_id:
        return
    if requester.id == protocol.signer_id:
        return
    if AccessPolicy.can_create_tests(requester):
        return
    raise AppError("Нет доступа к протоколу", status_code=403)


class SignProtocolHandler:
    def handle(self, command: SignProtocolCommand) -> SignedProtocolOut:
        if not AccessPolicy.can_create_tests(command.signer):
            raise AppError("Подписывать протокол может только admin или Еж", status_code=403)
        attempt = AttemptRepository.get_by_id_for_test(
            command.db, command.attempt_id, command.test_id
        )
        if not attempt:
            raise AppError("Попытка не найдена", status_code=404)
        if attempt.finished_at is None:
            raise AppError("Экзамен ещё не завершён", status_code=400)

        existing = ProtocolRepository.get_by_attempt_id(command.db, command.attempt_id)
        if existing:
            return _protocol_out(existing)

        examinee = UserRepository.get_by_id(command.db, attempt.user_id)
        test = TestRepository.get_by_id(command.db, attempt.test_id)
        if not examinee or not test:
            raise AppError("Недостаточно данных для подписания протокола", status_code=400)
        require_profile_complete(examinee)

        summary = score_attempt(command.db, attempt)
        if not exam_is_passed(summary.percent):
            raise AppError(
                "Протокол можно подписать только после успешной сдачи экзамена",
                status_code=400,
            )

        protocol = SignedProtocol(
            attempt_id=attempt.id,
            signer_id=command.signer.id,
            examinee_id=examinee.id,
            examinee_full_name=str(examinee.full_name),
            examinee_birth_date=examinee.birth_date,
            examinee_job_title=str(examinee.job_title),
            test_title=test.title,
            result_percent=int(summary.percent),
        )
        command.db.add(protocol)
        command.db.commit()
        command.db.refresh(protocol)
        return _protocol_out(protocol)


class GetSignedProtocolHandler:
    def handle(self, query: GetSignedProtocolQuery) -> SignedProtocolOut:
        protocol = ProtocolRepository.get_by_attempt_id(query.db, query.attempt_id)
        if not protocol:
            raise AppError("Протокол ещё не подписан", status_code=404)
        if protocol.attempt is None or protocol.attempt.test_id != query.test_id:
            raise AppError("Протокол не найден", status_code=404)
        _require_signed_protocol_reader(protocol, query.requester)
        return _protocol_out(protocol)


class GetSignedProtocolPdfHandler:
    def handle(self, query: GetSignedProtocolPdfQuery) -> bytes:
        protocol = ProtocolRepository.get_by_attempt_id(query.db, query.attempt_id)
        if not protocol:
            raise AppError("Протокол ещё не подписан", status_code=404)
        if protocol.attempt is None or protocol.attempt.test_id != query.test_id:
            raise AppError("Протокол не найден", status_code=404)
        _require_signed_protocol_reader(protocol, query.requester)
        return build_signed_protocol_pdf(query.db, protocol)


class GetAttemptProtocolFormPdfHandler:
    def handle(self, query: GetAttemptProtocolFormPdfQuery) -> bytes:
        _require_protocol_exporter(query.requester)
        attempt, examinee = _examinee_for_attempt(
            query.db, query.test_id, query.attempt_id
        )
        if attempt.finished_at is None:
            raise AppError("Экзамен ещё не завершён", status_code=400)

        test = TestRepository.get_by_id(query.db, attempt.test_id)
        if not test:
            raise AppError("Недостаточно данных для формирования протокола", status_code=400)

        summary = score_attempt(query.db, attempt)
        if not exam_is_passed(summary.percent):
            raise AppError(
                "Форму протокола можно выгрузить только после успешной сдачи экзамена",
                status_code=400,
            )

        return build_examinee_protocol_form_pdf(query.db, attempt, examinee, test)


class GetAttemptProtocolDraftPdfHandler:
    """Черновик из профиля экзаменуемого (как у Кота в кабинете)."""

    def handle(self, query: GetAttemptProtocolDraftPdfQuery) -> bytes:
        _require_protocol_exporter(query.requester)
        _attempt, examinee = _examinee_for_attempt(
            query.db, query.test_id, query.attempt_id
        )
        return build_protocol_pdf(query.db, examinee)
