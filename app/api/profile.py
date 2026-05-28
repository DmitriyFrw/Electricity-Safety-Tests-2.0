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
from app.schemas import AsyncTaskAcceptedOut, UserOut
from app.services.exports import ExportService
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


@router.post("/protocol.pdf/export", response_model=AsyncTaskAcceptedOut, status_code=202)
def start_protocol_export(user: Annotated[User, Depends(login_required)]):
    try:
        task_id = ProfileService.build_protocol_pdf_async(user)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e
    return AsyncTaskAcceptedOut(task_id=task_id, status="pending")


@router.post("/attempts/export", response_model=AsyncTaskAcceptedOut, status_code=202)
def start_attempts_export(
    user: Annotated[User, Depends(login_required)],
    test_id: int | None = None,
):
    task_id = ProfileService.export_attempts_async(user, test_id=test_id)
    return AsyncTaskAcceptedOut(task_id=task_id, status="pending")


@router.get("/exports/{task_id}")
def get_export_task(task_id: str, _user: Annotated[User, Depends(login_required)]):
    task = ExportService.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    if task.owner_user_id != _user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этой задаче экспорта")
    if task.status != "done":
        return {"task_id": task.task_id, "status": task.status, "error": task.error}
    return Response(
        content=task.payload or b"",
        media_type=task.content_type or "application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{task.filename or "export.bin"}"',
            "X-Task-Id": task.task_id,
        },
    )
