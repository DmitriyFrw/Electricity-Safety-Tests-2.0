from __future__ import annotations

from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session

from app.api.deps import login_required
from app.cqrs.bus import dispatch_command, dispatch_query
from app.cqrs.deps import get_query_bus
from app.cqrs.messages.exports import GetExportTaskQuery
from app.cqrs.messages.profile import (
    BuildProtocolPdfQuery,
    GetProfileQuery,
    StartAttemptsExportCommand,
    StartProtocolExportCommand,
    UpdateProfileCommand,
)
from app.database import get_db
from app.dto import ExportTaskDTO
from app.form_requests.profile import ProfileUpdateRequest
from app.models import User
from app.schemas import AsyncTaskAcceptedOut, UserOut

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=UserOut)
def get_profile(user: Annotated[User, Depends(login_required)]) -> UserOut:
    return dispatch_query(GetProfileQuery(user=user), UserOut)


@router.put("", response_model=UserOut)
def update_profile(
    form: ProfileUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
) -> UserOut:
    return dispatch_command(UpdateProfileCommand(db=db, user=user, form=form), UserOut)


@router.get("/protocol.pdf")
def download_protocol(
    user: Annotated[User, Depends(login_required)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    pdf_bytes = dispatch_query(BuildProtocolPdfQuery(db=db, user=user), bytes)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="protocol.pdf"'},
    )


@router.post("/protocol.pdf/export", response_model=AsyncTaskAcceptedOut, status_code=202)
def start_protocol_export(
    user: Annotated[User, Depends(login_required)],
    db: Annotated[Session, Depends(get_db)],
) -> AsyncTaskAcceptedOut:
    task_id = dispatch_command(StartProtocolExportCommand(db=db, user=user), str)
    return AsyncTaskAcceptedOut(task_id=task_id, status="pending")


@router.post("/attempts/export", response_model=AsyncTaskAcceptedOut, status_code=202)
def start_attempts_export(
    user: Annotated[User, Depends(login_required)],
    test_id: int | None = None,
) -> AsyncTaskAcceptedOut:
    task_id = dispatch_command(
        StartAttemptsExportCommand(user=user, test_id=test_id), str
    )
    return AsyncTaskAcceptedOut(task_id=task_id, status="pending")


@router.get("/exports/{task_id}", response_model=None)
def get_export_task(
    task_id: str, _user: Annotated[User, Depends(login_required)]
) -> Response:
    task = cast(
        ExportTaskDTO | None,
        get_query_bus().dispatch(GetExportTaskQuery(task_id=task_id)),
    )
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    if task.owner_user_id != _user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этой задаче экспорта")
    if task.status != "done":
        return JSONResponse(
            {"task_id": task.task_id, "status": task.status, "error": task.error}
        )
    return Response(
        content=task.payload or b"",
        media_type=task.content_type or "application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{task.filename or "export.bin"}"',
            "X-Task-Id": task.task_id,
        },
    )
