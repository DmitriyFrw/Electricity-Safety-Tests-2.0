from __future__ import annotations

import csv
import io
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.dto import ExportRequestDTO, ExportTaskDTO
from app.models import Attempt
from app.pdf_service import build_protocol_pdf


class ExportService:
    _tasks: dict[str, ExportTaskDTO] = {}
    _executor = ThreadPoolExecutor(max_workers=2)

    @classmethod
    def create_exam_results_export(cls, req: ExportRequestDTO) -> str:
        task_id = str(uuid.uuid4())
        cls._tasks[task_id] = ExportTaskDTO(task_id=task_id, status="pending")
        cls._executor.submit(cls._run_exam_export, task_id, req)
        return task_id

    @classmethod
    def create_protocol_export(cls, user) -> str:
        task_id = str(uuid.uuid4())
        cls._tasks[task_id] = ExportTaskDTO(task_id=task_id, status="pending")
        cls._executor.submit(cls._run_protocol_export, task_id, user)
        return task_id

    @classmethod
    def get_task(cls, task_id: str) -> ExportTaskDTO | None:
        task = cls._tasks.get(task_id)
        if not task:
            return None
        # auto-expire old completed tasks
        age = (datetime.now(timezone.utc) - task.created_at).total_seconds()
        if age > 3600 and task.status in {"done", "failed"}:
            cls._tasks.pop(task_id, None)
            return None
        return task

    @classmethod
    def _run_exam_export(cls, task_id: str, req: ExportRequestDTO) -> None:
        from app.database import SessionLocal

        task = cls._tasks[task_id]
        task.status = "running"
        db: Session = SessionLocal()
        try:
            q = db.query(Attempt).filter(Attempt.user_id == req.user_id, Attempt.finished_at.isnot(None))
            if req.test_id is not None:
                q = q.filter(Attempt.test_id == req.test_id)
            rows = q.order_by(Attempt.finished_at.desc()).all()

            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow(["attempt_id", "test_id", "mode", "started_at", "finished_at"])
            for row in rows:
                writer.writerow([row.id, row.test_id, row.mode, row.started_at, row.finished_at])
            task.payload = buf.getvalue().encode("utf-8")
            task.content_type = "text/csv; charset=utf-8"
            task.filename = "exam_results.csv"
            task.status = "done"
        except Exception as exc:  # pragma: no cover
            task.status = "failed"
            task.error = str(exc)
        finally:
            db.close()

    @classmethod
    def _run_protocol_export(cls, task_id: str, user) -> None:
        task = cls._tasks[task_id]
        task.status = "running"
        try:
            payload = build_protocol_pdf(user)
            task.payload = payload
            task.content_type = "application/pdf"
            task.filename = "protocol.pdf"
            task.status = "done"
        except Exception as exc:  # pragma: no cover
            task.status = "failed"
            task.error = str(exc)
