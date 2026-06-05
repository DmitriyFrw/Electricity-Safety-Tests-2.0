from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.api.deps import login_required
from app.cqrs.bus import dispatch_query
from app.cqrs.messages.manuals import GetManualPathQuery, ListManualsQuery
from app.models import User
from app.schemas import ManualOut

router = APIRouter(prefix="/manuals", tags=["manuals"])


@router.get("", response_model=list[ManualOut])
def list_manuals(_user: Annotated[User, Depends(login_required)]) -> list[ManualOut]:
    return dispatch_query(ListManualsQuery(), list[ManualOut])


@router.get("/{manual_id}")
def get_manual(
    manual_id: str,
    _user: Annotated[User, Depends(login_required)],
) -> FileResponse:
    path: Path | None = dispatch_query(GetManualPathQuery(manual_id=manual_id), Path)
    if not path:
        raise HTTPException(status_code=404, detail="Мануал не найден")
    return FileResponse(path, media_type="text/plain; charset=utf-8", filename=path.name)
