from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from typing import Any

import redis

from app.config import get_settings
from app.dto import ExportTaskDTO

logger = logging.getLogger("export-task-store")

_MEMORY: dict[str, ExportTaskDTO] = {}
_MEMORY_LOCK = threading.Lock()

_META_PREFIX = "export:meta:"
_PAYLOAD_PREFIX = "export:payload:"


def _redis_client() -> redis.Redis | None:
    url = get_settings().redis_url.strip()
    if not url:
        return None
    return redis.from_url(url, decode_responses=False)


def _meta_key(task_id: str) -> str:
    return f"{_META_PREFIX}{task_id}"


def _payload_key(task_id: str) -> str:
    return f"{_PAYLOAD_PREFIX}{task_id}"


def _ttl_seconds() -> int:
    return get_settings().export_task_ttl_seconds


def _encode_meta(task: ExportTaskDTO) -> dict[str, str]:
    return {
        "owner_user_id": str(task.owner_user_id),
        "status": task.status,
        "content_type": task.content_type or "",
        "filename": task.filename or "",
        "error": task.error or "",
        "created_at": task.created_at.isoformat(),
    }


def _payload_as_bytes(payload: bytes | str | None) -> bytes | None:
    if payload is None:
        return None
    return payload if isinstance(payload, bytes) else payload.encode()


def _decode_meta(
    task_id: str,
    raw: dict[bytes | str, bytes | str],
    payload: bytes | str | None,
) -> ExportTaskDTO:
    def _s(key: str) -> str:
        val = raw.get(key.encode(), b"")
        return val.decode() if isinstance(val, bytes) else str(val)

    created_raw = _s("created_at")
    created_at = datetime.fromisoformat(created_raw)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    content_type = _s("content_type") or None
    filename = _s("filename") or None
    error = _s("error") or None

    return ExportTaskDTO(
        task_id=task_id,
        owner_user_id=int(_s("owner_user_id")),
        status=_s("status") or "pending",
        content_type=content_type,
        filename=filename,
        payload=_payload_as_bytes(payload),
        error=error,
        created_at=created_at,
    )


def _apply_ttl(client: redis.Redis, task_id: str, status: str) -> None:
    if status in {"done", "failed"}:
        ttl = _ttl_seconds()
        if ttl > 0:
            client.expire(_meta_key(task_id), ttl)
            client.expire(_payload_key(task_id), ttl)


class ExportTaskStore:
    """Хранилище export-задач: Redis при наличии REDIS_URL, иначе in-memory (тесты/dev)."""

    @classmethod
    def put(cls, task: ExportTaskDTO) -> None:
        client = _redis_client()
        if client is None:
            with _MEMORY_LOCK:
                _MEMORY[task.task_id] = task
            return

        meta = _encode_meta(task)
        pipe = client.pipeline()
        pipe.hset(
            _meta_key(task.task_id),
            mapping={k.encode(): v.encode() for k, v in meta.items()},
        )
        if task.payload is not None:
            pipe.set(_payload_key(task.task_id), task.payload)
        pipe.execute()
        _apply_ttl(client, task.task_id, task.status)

    @classmethod
    def get(cls, task_id: str) -> ExportTaskDTO | None:
        client = _redis_client()
        if client is None:
            with _MEMORY_LOCK:
                return _MEMORY.get(task_id)

        raw = client.hgetall(_meta_key(task_id))
        if not raw:
            return None
        payload = client.get(_payload_key(task_id))
        return _decode_meta(task_id, raw, payload)

    @classmethod
    def delete(cls, task_id: str) -> None:
        client = _redis_client()
        if client is None:
            with _MEMORY_LOCK:
                _MEMORY.pop(task_id, None)
            return
        client.delete(_meta_key(task_id), _payload_key(task_id))

    @classmethod
    def patch(cls, task_id: str, **updates: Any) -> ExportTaskDTO | None:
        task = cls.get(task_id)
        if not task:
            return None
        for key, value in updates.items():
            if hasattr(task, key):
                setattr(task, key, value)
        cls.put(task)
        return task

    @classmethod
    def backend_name(cls) -> str:
        return "redis" if _redis_client() is not None else "memory"
