from __future__ import annotations

from sqlalchemy.orm import Session

from app.support.grading import exam_is_passed
from app.models import SignedProtocol, User
from app.policies import AccessPolicy
from app.repositories import AttemptRepository, ProtocolRepository, TestRepository, UserRepository
from app.services.attempts.scoring import score_attempt
from app.services.pdf.protocol import build_signed_protocol_pdf
from app.support.errors import AppError
from app.support.profile import require_profile_complete
from app.schemas import SignedProtocolOut


class TestProtocolService:
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
    def sign_protocol(
        db: Session, test_id: int, attempt_id: int, signer: User
    ) -> SignedProtocolOut:
        if not AccessPolicy.can_create_tests(signer):
            raise AppError("Подписывать протокол может только admin или Еж", status_code=403)
        attempt = AttemptRepository.get_by_id_for_test(db, attempt_id, test_id)
        if not attempt:
            raise AppError("Попытка не найдена", status_code=404)
        if attempt.finished_at is None:
            raise AppError("Экзамен ещё не завершён", status_code=400)

        existing = ProtocolRepository.get_by_attempt_id(db, attempt_id)
        if existing:
            return TestProtocolService._protocol_out(existing)

        examinee = UserRepository.get_by_id(db, attempt.user_id)
        test = TestRepository.get_by_id(db, attempt.test_id)
        if not examinee or not test:
            raise AppError("Недостаточно данных для подписания протокола", status_code=400)
        require_profile_complete(examinee)

        summary = score_attempt(db, attempt)
        if not exam_is_passed(summary.percent):
            raise AppError(
                "Протокол можно подписать только после успешной сдачи экзамена",
                status_code=400,
            )

        protocol = SignedProtocol(
            attempt_id=attempt.id,
            signer_id=signer.id,
            examinee_id=examinee.id,
            examinee_full_name=examinee.full_name,  # type: ignore[arg-type]
            examinee_birth_date=examinee.birth_date,  # type: ignore[arg-type]
            examinee_job_title=examinee.job_title,  # type: ignore[arg-type]
            test_title=test.title,
            result_percent=int(summary.percent),
        )
        db.add(protocol)
        db.commit()
        db.refresh(protocol)
        return TestProtocolService._protocol_out(protocol)

    @staticmethod
    def _require_signed_protocol_reader(protocol: SignedProtocol, requester: User) -> None:
        if requester.id == protocol.examinee_id:
            return
        if requester.id == protocol.signer_id:
            return
        if AccessPolicy.can_create_tests(requester):
            return
        raise AppError("Нет доступа к протоколу", status_code=403)

    @staticmethod
    def get_signed_protocol(
        db: Session, test_id: int, attempt_id: int, requester: User
    ) -> SignedProtocolOut:
        protocol = ProtocolRepository.get_by_attempt_id(db, attempt_id)
        if not protocol:
            raise AppError("Протокол ещё не подписан", status_code=404)
        if protocol.attempt is None or protocol.attempt.test_id != test_id:
            raise AppError("Протокол не найден", status_code=404)
        TestProtocolService._require_signed_protocol_reader(protocol, requester)
        return TestProtocolService._protocol_out(protocol)

    @staticmethod
    def get_signed_protocol_pdf(
        db: Session, test_id: int, attempt_id: int, requester: User
    ) -> bytes:
        protocol = ProtocolRepository.get_by_attempt_id(db, attempt_id)
        if not protocol:
            raise AppError("Протокол ещё не подписан", status_code=404)
        if protocol.attempt is None or protocol.attempt.test_id != test_id:
            raise AppError("Протокол не найден", status_code=404)
        TestProtocolService._require_signed_protocol_reader(protocol, requester)
        return build_signed_protocol_pdf(db, protocol)
