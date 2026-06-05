from __future__ import annotations

import csv
import io
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.dto import ExportRequestDTO, ExportTaskDTO
from app.models import Attempt, User
from app.config import get_settings
from app.services.pdf.protocol import build_protocol_pdf
from app.services.exports.task_store import ExportTaskStore


class ExportService:
    _executor = ThreadPoolExecutor(max_workers=2)

    @classmethod
    def create_exam_results_export(cls, req: ExportRequestDTO) -> str:
        task_id = str(uuid.uuid4())
        ExportTaskStore.put(
            ExportTaskDTO(task_id=task_id, owner_user_id=req.user_id, status="pending")
        )
        cls._executor.submit(cls._run_exam_export, task_id, req)
        return task_id

    @classmethod
    def create_protocol_export(cls, user_id: int) -> str:
        task_id = str(uuid.uuid4())
        ExportTaskStore.put(
            ExportTaskDTO(task_id=task_id, owner_user_id=user_id, status="pending")
        )
        cls._executor.submit(cls._run_protocol_export, task_id, user_id)
        return task_id

    @classmethod
    def get_task(cls, task_id: str) -> ExportTaskDTO | None:
        task = ExportTaskStore.get(task_id)
        if not task:
            return None
        age = (datetime.now(timezone.utc) - task.created_at).total_seconds()
        ttl = get_settings().export_task_ttl_seconds
        if age > ttl and task.status in {"done", "failed"}:
            ExportTaskStore.delete(task_id)
            return None
        return task

    @classmethod
    def _run_exam_export(cls, task_id: str, req: ExportRequestDTO) -> None:
        from app.database import SessionLocal

        ExportTaskStore.patch(task_id, status="running")
        db: Session = SessionLocal()
        try:
            q = db.query(Attempt).filter(
                Attempt.user_id == req.user_id, Attempt.finished_at.isnot(None)
            )
            if req.test_id is not None:
                q = q.filter(Attempt.test_id == req.test_id)
            rows = q.order_by(Attempt.finished_at.desc()).all()

            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow(["attempt_id", "test_id", "mode", "started_at", "finished_at"])
            for row in rows:
                writer.writerow([row.id, row.test_id, row.mode, row.started_at, row.finished_at])
            ExportTaskStore.patch(
                task_id,
                payload=buf.getvalue().encode("utf-8"),
                content_type="text/csv; charset=utf-8",
                filename="exam_results.csv",
                status="done",
            )
        except Exception as exc:  # pragma: no cover
            ExportTaskStore.patch(task_id, status="failed", error=str(exc))
        finally:
            db.close()

    @classmethod
    def _run_protocol_export(cls, task_id: str, user_id: int) -> None:
        from app.database import SessionLocal
        from app.support.profile import require_profile_complete

        ExportTaskStore.patch(task_id, status="running")
        db = SessionLocal()
        try:
            user = db.get(User, user_id)
            if user is None:
                raise ValueError("Пользователь не найден")
            require_profile_complete(user)
            payload = build_protocol_pdf(db, user)
            ExportTaskStore.patch(
                task_id,
                payload=payload,
                content_type="application/pdf",
                filename="protocol.pdf",
                status="done",
            )
        except Exception as exc:  # pragma: no cover
            ExportTaskStore.patch(task_id, status="failed", error=str(exc))
        finally:
            db.close()
