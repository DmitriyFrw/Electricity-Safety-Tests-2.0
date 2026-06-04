from __future__ import annotations

from sqlalchemy.orm import Session

from app.api.mappers import dashboard_out
from app.models import User
from app.repositories import AttemptRepository, ProtocolRepository, TestRepository
from app.schemas import DashboardOut


class DashboardService:
    @staticmethod
    def get_dashboard(db: Session, user: User) -> DashboardOut:
        created = TestRepository.list_by_author(db, user.id)
        attempts = AttemptRepository.list_finished_for_user(db, user.id)
        signed_protocol = ProtocolRepository.get_latest_for_examinee(db, user.id)
        return dashboard_out(
            db,
            user,
            created_tests=created,
            attempts=attempts,
            signed_protocol=signed_protocol,
        )
