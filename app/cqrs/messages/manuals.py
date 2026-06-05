from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.cqrs.base import Query


@dataclass(frozen=True, slots=True)
class ListManualsQuery(Query):
    pass


@dataclass(frozen=True, slots=True)
class GetManualPathQuery(Query):
    manual_id: str
