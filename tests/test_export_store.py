from __future__ import annotations

from app.dto import ExportTaskDTO
from app.services.exports.task_store import ExportTaskStore


def test_export_task_store_memory_roundtrip(monkeypatch):
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.setenv("REDIS_URL", "")

    task_id = "task-0001"
    task = ExportTaskDTO(task_id=task_id, owner_user_id=42, status="pending")
    ExportTaskStore.put(task)
    loaded = ExportTaskStore.get(task_id)
    assert loaded is not None
    assert loaded.owner_user_id == 42

    ExportTaskStore.patch(task_id, status="done", payload=b"ok", filename="x.csv")
    done = ExportTaskStore.get(task_id)
    assert done is not None
    assert done.status == "done"
    assert done.payload == b"ok"

    ExportTaskStore.delete(task_id)
    assert ExportTaskStore.get(task_id) is None
