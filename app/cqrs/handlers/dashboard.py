from __future__ import annotations

from app.api.mappers import dashboard_out
from app.constants import DASHBOARD_ATTEMPTS_PAGE_SIZE
from app.cqrs.messages.dashboard import GetDashboardQuery
from app.repositories import AttemptRepository, ProtocolRepository, TestRepository
from app.schemas import DashboardOut


class GetDashboardHandler:
    def handle(self, query: GetDashboardQuery) -> DashboardOut:
        query.db.refresh(query.user)
        created = TestRepository.list_by_author(query.db, query.user.id)
        attempts_total = AttemptRepository.count_finished_for_user(query.db, query.user.id)
        attempts = AttemptRepository.list_finished_for_user(
            query.db,
            query.user.id,
            limit=DASHBOARD_ATTEMPTS_PAGE_SIZE,
        )
        signed_protocol = ProtocolRepository.get_latest_for_examinee(query.db, query.user.id)
        return dashboard_out(
            query.db,
            query.user,
            created_tests=created,
            attempts=attempts,
            attempts_total=attempts_total,
            signed_protocol=signed_protocol,
        )
