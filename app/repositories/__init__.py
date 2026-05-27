from __future__ import annotations

from sqlalchemy.orm import Session, selectinload

from app.models import Attempt, Test, Ticket, User

# Eager-loading options (единый источник для избежания N+1)
TEST_WITH_TICKETS = selectinload(Test.tickets).selectinload(Ticket.questions)
TEST_WITH_AUTHOR = selectinload(Test.author)
TEST_LIST_OPTIONS = (TEST_WITH_AUTHOR, selectinload(Test.tickets))
TEST_FULL_OPTIONS = (TEST_WITH_AUTHOR, TEST_WITH_TICKETS)

ATTEMPT_DASHBOARD_OPTIONS = (
    selectinload(Attempt.test),
    selectinload(Attempt.user_answers),
)


class TestRepository:
    @staticmethod
    def get_by_id(db: Session, test_id: int) -> Test | None:
        return db.get(Test, test_id)

    @staticmethod
    def get_full(db: Session, test_id: int) -> Test | None:
        return (
            db.query(Test)
            .options(*TEST_FULL_OPTIONS)
            .filter(Test.id == test_id)
            .one_or_none()
        )

    @staticmethod
    def list_all(db: Session) -> list[Test]:
        return db.query(Test).options(*TEST_LIST_OPTIONS).order_by(Test.created_at.desc()).all()

    @staticmethod
    def list_by_author(db: Session, author_id: int) -> list[Test]:
        return (
            db.query(Test)
            .options(selectinload(Test.tickets))
            .filter(Test.author_id == author_id)
            .order_by(Test.created_at.desc())
            .all()
        )


class UserRepository:
    @staticmethod
    def get_by_username(db: Session, username: str) -> User | None:
        return db.query(User).filter(User.username == username).one_or_none()

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> User | None:
        return db.get(User, user_id)


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
