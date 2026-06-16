from __future__ import annotations

from app.api.mappers import test_list_out_from_catalog
from app.cache import cached, invalidate_cache
from app.cqrs.messages.tests import CreateTestCommand, ListTestsQuery
from app.constants import ROLE_KOT
from app.models import Test
from app.repositories.catalog import list_catalog_snapshots
from app.schemas import TestCreateOut, TestListOut
from app.support.safety_groups import effective_safety_group


def _test_list_cache_key(query: ListTestsQuery) -> str:
    return (
        f"user:{query.user.id}:role:{query.user.role}"
        f":group:{effective_safety_group(query.user)}"
    )


@cached("test_list", key_fn=_test_list_cache_key)
def _list_tests(query: ListTestsQuery) -> TestListOut:
    snapshots = list_catalog_snapshots(query.db)
    if query.user.role == ROLE_KOT:
        group = effective_safety_group(query.user)
        snapshots = [
            s
            for s in snapshots
            if s.test.safety_group == group and s.test.published
        ]
    return test_list_out_from_catalog(snapshots, query.user)


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
