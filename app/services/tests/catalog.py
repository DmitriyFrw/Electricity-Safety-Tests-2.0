from __future__ import annotations

from sqlalchemy.orm import Session

from app.api.mappers import test_list_out
from app.cache import cached, invalidate_cache
from app.form_requests.tests import TestCreateRequest
from app.models import Test, User
from app.repositories import TestRepository
from app.schemas import TestCreateOut, TestListOut


class TestCatalogService:
    @staticmethod
    @cached("test_list", key_fn=lambda db, user: f"user:{user.id}")
    def list_tests(db: Session, user: User) -> TestListOut:
        tests = TestRepository.list_all(db)
        return test_list_out(db, tests, user)

    @staticmethod
    def create_test(db: Session, user: User, form: TestCreateRequest) -> TestCreateOut:
        test = Test(
            author_id=user.id,
            title=form.title,
            description=form.description,
        )
        db.add(test)
        db.commit()
        db.refresh(test)
        invalidate_cache("test_list")
        return TestCreateOut(id=test.id, title=test.title)
