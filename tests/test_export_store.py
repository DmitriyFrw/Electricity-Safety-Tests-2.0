from __future__ import annotations

from app.dto import ExportTaskDTO
from app.services.exports.task_store import ExportTaskStore


def test_export_task_store_memory_roundtrip(monkeypatch):
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.setenv("REDIS_URL", "")

    task = ExportTaskDTO(task_id="t1", owner_user_id=42, status="pending")
    ExportTaskStore.put(task)
    loaded = ExportTaskStore.get("t1")
    assert loaded is not None
    assert loaded.owner_user_id == 42

    ExportTaskStore.patch("t1", status="done", payload=b"ok", filename="x.csv")
    done = ExportTaskStore.get("t1")
    assert done is not None
    assert done.status == "done"
    assert done.payload == b"ok"

    ExportTaskStore.delete("t1")
    assert ExportTaskStore.get("t1") is None
