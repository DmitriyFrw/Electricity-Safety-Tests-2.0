from __future__ import annotations

from app.api.mappers import test_list_out
from app.cache import cached, invalidate_cache
from app.cqrs.messages.tests import CreateTestCommand, ListTestsQuery
from app.models import Test
from app.repositories import TestRepository
from app.schemas import TestCreateOut, TestListOut


@cached("test_list", key_fn=lambda query: f"user:{query.user.id}")
def _list_tests(query: ListTestsQuery) -> TestListOut:
    tests = TestRepository.list_all(query.db)
    return test_list_out(query.db, tests, query.user)


class ListTestsHandler:
    def handle(self, query: ListTestsQuery) -> TestListOut:
        return _list_tests(query)


class CreateTestHandler:
    def handle(self, command: CreateTestCommand) -> TestCreateOut:
        test = Test(
            author_id=command.user.id,
            title=command.form.title,
            description=command.form.description,
        )
        command.db.add(test)
        command.db.commit()
        command.db.refresh(test)
        invalidate_cache("test_list")
        return TestCreateOut(id=test.id, title=test.title)
