from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import login_required
from app.exceptions import AppError
from app.form_requests.profile import ProfileUpdateRequest
from app.models import User
from app.schemas import UserOut
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=UserOut)
def get_profile(user: Annotated[User, Depends(login_required)]):
    return ProfileService.get_profile(user)


@router.put("", response_model=UserOut)
def update_profile(
    form: ProfileUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
):
    try:
        return ProfileService.update_profile(db, user, form)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e


@router.get("/protocol.pdf")
def download_protocol(user: Annotated[User, Depends(login_required)]):
    try:
        pdf_bytes = ProfileService.build_protocol_pdf(user)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="protocol.pdf"'},
    )
