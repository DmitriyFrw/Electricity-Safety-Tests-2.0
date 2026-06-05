from __future__ import annotations

from pathlib import Path

from app.cqrs.bus import dispatch_query
from app.cqrs.messages.manuals import GetManualPathQuery, ListManualsQuery
from app.schemas import ManualOut


class ManualService:
    @staticmethod
    def list_manuals() -> list[ManualOut]:
        return dispatch_query(ListManualsQuery(), list[ManualOut])

    @staticmethod
    def get_manual_path(manual_id: str) -> Path | None:
        return dispatch_query(GetManualPathQuery(manual_id=manual_id), Path)
