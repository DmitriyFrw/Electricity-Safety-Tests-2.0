from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models import Test
from app.repositories.test_repository import TestRepository
from app.support.validation import test_is_available_loaded, test_is_ready_loaded


@dataclass(frozen=True, slots=True)
class CatalogTestSnapshot:
    test: Test
    ticket_count: int
    published: bool
    content_complete: bool
    ready: bool


def list_catalog_snapshots(db: Session) -> list[CatalogTestSnapshot]:
    """Каталог тестов: eager loading tickets/questions и готовые подсчёты без N+1."""
    tests = TestRepository.list_catalog(db)
    return [
        CatalogTestSnapshot(
            test=t,
            ticket_count=len(t.tickets),
            published=bool(t.published),
            content_complete=test_is_ready_loaded(t),
            ready=test_is_available_loaded(t),
        )
        for t in tests
    ]
