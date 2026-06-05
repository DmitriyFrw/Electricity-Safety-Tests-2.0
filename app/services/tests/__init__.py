"""Legacy *Service classes — логика в app/cqrs/handlers/. Не использовать в новом коде."""

from app.services.tests.catalog import TestCatalogService
from app.services.tests.editor import TestEditorService
from app.services.tests.exam import TestExamService
from app.services.tests.protocols import TestProtocolService
from app.services.tests.training import TestTrainingService

__all__ = [
    "TestCatalogService",
    "TestEditorService",
    "TestExamService",
    "TestProtocolService",
    "TestTrainingService",
]
