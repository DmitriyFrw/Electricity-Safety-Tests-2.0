from __future__ import annotations

from typing import Protocol


class SessionStore(Protocol):
    """Порт сессии: сервисы не зависят от FastAPI/Starlette Request."""

    def get(self, key: str) -> object | None: ...

    def set(self, key: str, value: object) -> None: ...

    def clear(self) -> None: ...
