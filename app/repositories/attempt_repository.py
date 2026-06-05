from __future__ import annotations

from sqlalchemy.orm import Session

from app.constants import ATTEMPT_MODE_EXAM, ROLE_ADMIN
from app.models import Attempt, Test, User
from app.repositories.options import ATTEMPT_DASHBOARD_OPTIONS, ATTEMPT_STAFF_PROTOCOL_OPTIONS


class AttemptRepository:
    @staticmethod
    def list_finished_for_user(db: Session, user_id: int, *, limit: int = 100) -> list[Attempt]:
        return (
            db.query(Attempt)
            .options(*ATTEMPT_DASHBOARD_OPTIONS)
            .filter(Attempt.user_id == user_id, Attempt.finished_at.isnot(None))
            .order_by(Attempt.finished_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_open_exam(db: Session, *, user_id: int, test_id: int) -> Attempt | None:
        return (
            db.query(Attempt)
            .filter(
                Attempt.user_id == user_id,
                Attempt.test_id == test_id,
                Attempt.mode == ATTEMPT_MODE_EXAM,
                Attempt.finished_at.is_(None),
            )
            .order_by(Attempt.started_at.desc())
            .first()
        )

    @staticmethod
    def get_by_id_for_test(db: Session, attempt_id: int, test_id: int) -> Attempt | None:
        return (
            db.query(Attempt)
            .filter(Attempt.id == attempt_id, Attempt.test_id == test_id)
            .one_or_none()
        )

    @staticmethod
    def list_finished_exam_for_staff(
        db: Session, staff: User, *, limit: int = 50
    ) -> list[Attempt]:
        q = (
            db.query(Attempt)
            .options(*ATTEMPT_STAFF_PROTOCOL_OPTIONS)
            .join(Test, Attempt.test_id == Test.id)
            .filter(
                Attempt.mode == ATTEMPT_MODE_EXAM,
                Attempt.finished_at.isnot(None),
            )
        )
        if staff.role != ROLE_ADMIN:
            q = q.filter(Test.author_id == staff.id)
        return q.order_by(Attempt.finished_at.desc()).limit(limit).all()
