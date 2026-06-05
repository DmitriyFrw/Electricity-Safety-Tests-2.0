from __future__ import annotations

from typing import Protocol, TypeVar

from app.cqrs.base import Command, Query

C_contra = TypeVar("C_contra", bound=Command, contravariant=True)
Q_contra = TypeVar("Q_contra", bound=Query, contravariant=True)
R_co = TypeVar("R_co", covariant=True)


class CommandHandler(Protocol[C_contra, R_co]):
    def handle(self, command: C_contra) -> R_co: ...


class QueryHandler(Protocol[Q_contra, R_co]):
    def handle(self, query: Q_contra) -> R_co: ...
