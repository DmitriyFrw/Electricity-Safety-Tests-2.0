from __future__ import annotations

from collections.abc import MutableMapping
from dataclasses import dataclass

from fastapi import Request

from app.ports.session_store import SessionStore


class StarletteSessionStore:
    """Адаптер Starlette session → SessionStore."""

    def __init__(self, session: MutableMapping[str, object]) -> None:
        self._session = session

    def get(self, key: str) -> object | None:
        return self._session.get(key)

    def set(self, key: str, value: object) -> None:
        self._session[key] = value

    def clear(self) -> None:
        self._session.clear()


@dataclass(frozen=True, slots=True)
class HttpContext:
    """HTTP-контекст запроса без привязки сервисов к FastAPI."""

    session: SessionStore
    client_ip: str | None

    @classmethod
    def from_request(cls, request: Request) -> HttpContext:
        return cls(
            session=StarletteSessionStore(request.session),
            client_ip=request.client.host if request.client else None,
        )
