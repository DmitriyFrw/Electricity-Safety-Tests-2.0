from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Test
from app.repositories.options import TEST_FULL_OPTIONS, TEST_LIST_OPTIONS
from app.support.errors import AppError


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
    def get_full_or_raise(db: Session, test_id: int) -> Test:
        test = TestRepository.get_full(db, test_id)
        if not test:
            raise AppError("Тест не найден", status_code=404)
        return test

    @staticmethod
    def list_all(db: Session) -> list[Test]:
        return db.query(Test).options(*TEST_LIST_OPTIONS).order_by(Test.created_at.desc()).all()

    @staticmethod
    def list_by_author(db: Session, author_id: int) -> list[Test]:
        from sqlalchemy.orm import selectinload

        return (
            db.query(Test)
            .options(selectinload(Test.tickets))
            .filter(Test.author_id == author_id)
            .order_by(Test.created_at.desc())
            .all()
        )
