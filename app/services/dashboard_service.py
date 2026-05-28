from __future__ import annotations

from sqlalchemy.orm import Session, selectinload

from app.api_serializers import dashboard_out
from app.models import SignedProtocol, User
from app.repositories import AttemptRepository, TestRepository
from app.schemas import DashboardOut


class DashboardService:
    @staticmethod
    def get_dashboard(db: Session, user: User) -> DashboardOut:
        created = TestRepository.list_by_author(db, user.id)
        attempts = AttemptRepository.list_finished_for_user(db, user.id)
        signed_protocol = (
            db.query(SignedProtocol)
            .options(selectinload(SignedProtocol.attempt), selectinload(SignedProtocol.signer))
            .filter(SignedProtocol.examinee_id == user.id)
            .order_by(SignedProtocol.signed_at.desc())
            .first()
        )
        return dashboard_out(
            db,
            user,
            created_tests=created,
            attempts=attempts,
            signed_protocol=signed_protocol,
        )
