from __future__ import annotations

from unittest.mock import patch

from app.dto import ExportTaskDTO
from app.services.exports.export_service import ExportService
from app.services.exports.task_store import ExportTaskStore


def test_export_service_recovers_pending_tasks(monkeypatch):
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.setenv("REDIS_URL", "")

    ExportTaskStore.put(
        ExportTaskDTO(
            task_id="recover-1",
            owner_user_id=9,
            status="running",
            kind="exam_results",
            export_test_id=2,
        )
    )

    with patch.object(ExportService, "_dispatch_exam_export") as dispatch_exam:
        ExportService.recover_on_startup()
        dispatch_exam.assert_called_once()
        task_id, req = dispatch_exam.call_args.args
        assert task_id == "recover-1"
        assert req.user_id == 9
        assert req.test_id == 2

    patched = ExportTaskStore.get("recover-1")
    assert patched is not None
    assert patched.status == "pending"
