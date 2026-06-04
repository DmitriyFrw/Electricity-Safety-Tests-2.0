from __future__ import annotations

import datetime as dt


def ensure_utc_aware(value: dt.datetime) -> dt.datetime:
    """Нормализует datetime к UTC aware (SQLite в тестах отдаёт naive)."""
    if value.tzinfo is None:
        return value.replace(tzinfo=dt.timezone.utc)
    return value.astimezone(dt.timezone.utc)


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)
