from __future__ import annotations

import re
from pathlib import Path

from app.cache import cached
from app.cqrs.messages.manuals import GetManualPathQuery, ListManualsQuery
from app.schemas import ManualOut

MANUALS_DIR = Path(__file__).resolve().parent.parent.parent / "static" / "manuals"

MANUAL_TITLES: dict[str, str] = {
    "01_electrical_safety_basics.txt": "Основы электробезопасности",
    "02_first_aid.txt": "Первая помощь при поражении током",
    "03_protective_equipment.txt": "Средства индивидуальной защиты",
}

_MANUAL_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,127}$")


def _allowed_manual_ids() -> frozenset[str]:
    MANUALS_DIR.mkdir(parents=True, exist_ok=True)
    return frozenset(path.stem for path in MANUALS_DIR.glob("*.txt"))


def _resolve_manual_path(manual_id: str) -> Path | None:
    if not _MANUAL_ID_RE.fullmatch(manual_id):
        return None
    if manual_id not in _allowed_manual_ids():
        return None
    path = (MANUALS_DIR / f"{manual_id}.txt").resolve()
    if MANUALS_DIR.resolve() not in path.parents:
        return None
    return path if path.is_file() else None


@cached("manuals_list", key_fn=lambda query: "all")
def _list_manuals_cached(query: ListManualsQuery) -> list[ManualOut]:
    MANUALS_DIR.mkdir(parents=True, exist_ok=True)
    items: list[ManualOut] = []
    for path in sorted(MANUALS_DIR.glob("*.txt")):
        items.append(
            ManualOut(
                id=path.stem,
                title=MANUAL_TITLES.get(path.name, path.stem.replace("_", " ")),
                filename=path.name,
            )
        )
    return items


class ListManualsHandler:
    def handle(self, query: ListManualsQuery) -> list[ManualOut]:
        return _list_manuals_cached(query)


class GetManualPathHandler:
    def handle(self, query: GetManualPathQuery) -> Path | None:
        return _resolve_manual_path(query.manual_id.strip())
