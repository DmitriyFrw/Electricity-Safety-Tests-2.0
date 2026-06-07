from __future__ import annotations

from app.api.mappers import test_list_out
from app.cache import cached, invalidate_cache
from app.cqrs.messages.tests import CreateTestCommand, ListTestsQuery
from app.constants import ROLE_KOT
from app.models import Test
from app.repositories import TestRepository
from app.schemas import TestCreateOut, TestListOut
from app.support.safety_groups import effective_safety_group


@cached("test_list", key_fn=lambda query: f"user:{query.user.id}")
def _list_tests(query: ListTestsQuery) -> TestListOut:
    tests = TestRepository.list_all(query.db)
    if query.user.role == ROLE_KOT:
        group = effective_safety_group(query.user)
        tests = [t for t in tests if t.safety_group == group]
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
            safety_group=command.form.safety_group,
        )
        command.db.add(test)
        command.db.commit()
        command.db.refresh(test)
        invalidate_cache("test_list")
        return TestCreateOut(id=test.id, title=test.title, safety_group=test.safety_group)
