from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import SignedProtocol
from app.repositories.options import SIGNED_PROTOCOL_OPTIONS


class ProtocolRepository:
    @staticmethod
    def get_by_attempt_id(db: Session, attempt_id: int) -> SignedProtocol | None:
        return (
            db.query(SignedProtocol)
            .options(*SIGNED_PROTOCOL_OPTIONS)
            .filter(SignedProtocol.attempt_id == attempt_id)
            .one_or_none()
        )

    @staticmethod
    def get_latest_for_examinee(db: Session, examinee_id: int) -> SignedProtocol | None:
        return (
            db.query(SignedProtocol)
            .options(*SIGNED_PROTOCOL_OPTIONS)
            .filter(SignedProtocol.examinee_id == examinee_id)
            .order_by(SignedProtocol.signed_at.desc())
            .first()
        )
