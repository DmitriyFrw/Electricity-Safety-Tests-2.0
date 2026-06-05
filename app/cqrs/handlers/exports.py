from __future__ import annotations

from app.cqrs.messages.exports import (
    CreateExamResultsExportCommand,
    CreateProtocolExportCommand,
    GetExportTaskQuery,
)
from app.dto import ExportTaskDTO
from app.services.exports.export_service import ExportService


class CreateExamResultsExportHandler:
    def handle(self, command: CreateExamResultsExportCommand) -> str:
        return ExportService.create_exam_results_export(command.request)


class CreateProtocolExportHandler:
    def handle(self, command: CreateProtocolExportCommand) -> str:
        return ExportService.create_protocol_export(command.user.id)


class GetExportTaskHandler:
    def handle(self, query: GetExportTaskQuery) -> ExportTaskDTO | None:
        return ExportService.get_task(query.task_id)
