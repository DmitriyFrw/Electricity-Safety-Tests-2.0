from __future__ import annotations

from pathlib import Path

from app.cache import cached
from app.schemas import ManualOut

MANUALS_DIR = Path(__file__).resolve().parent.parent / "static" / "manuals"

MANUAL_TITLES: dict[str, str] = {
    "01_electrical_safety_basics.txt": "Основы электробезопасности",
    "02_first_aid.txt": "Первая помощь при поражении током",
    "03_protective_equipment.txt": "Средства индивидуальной защиты",
}


class ManualService:
    @staticmethod
    @cached("manuals_list")
    def list_manuals() -> list[ManualOut]:
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

    @staticmethod
    def get_manual_path(manual_id: str) -> Path | None:
        path = MANUALS_DIR / f"{manual_id}.txt"
        return path if path.is_file() else None
