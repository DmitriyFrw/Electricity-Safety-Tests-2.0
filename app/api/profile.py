from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api_serializers import user_out
from app.constants import ROLE_KOT
from app.database import get_db
from app.deps import login_required
from app.models import User
from app.pdf_service import build_protocol_pdf
from app.schemas import ProfileUpdateIn, UserOut

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=UserOut)
def get_profile(user: Annotated[User, Depends(login_required)]):
    return user_out(user)


@router.put("", response_model=UserOut)
def update_profile(
    body: ProfileUpdateIn,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
):
    if user.role != ROLE_KOT:
        raise HTTPException(
            status_code=403,
            detail="Редактирование профиля для PDF доступно только роли Кот",
        )
    user.full_name = body.full_name.strip()
    user.birth_date = body.birth_date
    user.job_title = body.job_title.strip()
    db.commit()
    db.refresh(user)
    return user_out(user)


@router.get("/protocol.pdf")
def download_protocol(user: Annotated[User, Depends(login_required)]):
    if user.role != ROLE_KOT:
        raise HTTPException(
            status_code=403,
            detail="Формирование протокола доступно только роли Кот",
        )
    if not user.full_name or not user.birth_date or not user.job_title:
        raise HTTPException(
            status_code=400,
            detail="Заполните ФИО, дату рождения и должность в личном кабинете",
        )
    pdf_bytes = build_protocol_pdf(user)
    filename = "protocol.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
