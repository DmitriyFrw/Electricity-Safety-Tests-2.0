from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.deps import login_required
from app.models import User
from app.schemas import ManualOut

router = APIRouter(prefix="/manuals", tags=["manuals"])

MANUALS_DIR = Path(__file__).resolve().parent.parent / "static" / "manuals"

MANUAL_TITLES: dict[str, str] = {
    "01_electrical_safety_basics.txt": "Основы электробезопасности",
    "02_first_aid.txt": "Первая помощь при поражении током",
    "03_protective_equipment.txt": "Средства индивидуальной защиты",
}


@router.get("", response_model=list[ManualOut])
def list_manuals(_user: Annotated[User, Depends(login_required)]):
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


@router.get("/{manual_id}")
def get_manual(
    manual_id: str,
    _user: Annotated[User, Depends(login_required)],
):
    path = MANUALS_DIR / f"{manual_id}.txt"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Мануал не найден")
    return FileResponse(path, media_type="text/plain; charset=utf-8", filename=path.name)
