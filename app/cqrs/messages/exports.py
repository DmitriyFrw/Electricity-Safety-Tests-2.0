from __future__ import annotations

from dataclasses import dataclass

from app.cqrs.base import Command, Query
from app.dto import ExportRequestDTO, ExportTaskDTO
from app.models import User


@dataclass(frozen=True, slots=True)
class CreateExamResultsExportCommand(Command):
    request: ExportRequestDTO


@dataclass(frozen=True, slots=True)
class CreateProtocolExportCommand(Command):
    user: User


@dataclass(frozen=True, slots=True)
class GetExportTaskQuery(Query):
    task_id: str
