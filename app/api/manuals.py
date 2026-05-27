from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.deps import login_required
from app.models import User
from app.schemas import ManualOut
from app.services.manual_service import ManualService

router = APIRouter(prefix="/manuals", tags=["manuals"])


@router.get("", response_model=list[ManualOut])
def list_manuals(_user: Annotated[User, Depends(login_required)]):
    return ManualService.list_manuals()


@router.get("/{manual_id}")
def get_manual(
    manual_id: str,
    _user: Annotated[User, Depends(login_required)],
):
    path = ManualService.get_manual_path(manual_id)
    if not path:
        raise HTTPException(status_code=404, detail="Мануал не найден")
    return FileResponse(path, media_type="text/plain; charset=utf-8", filename=path.name)
