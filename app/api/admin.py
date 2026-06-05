from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import admin_required
from app.cqrs.bus import dispatch_command, dispatch_query
from app.cqrs.messages.admin import (
    GetUserProtocolDraftPdfQuery,
    ListUsersQuery,
    UpdateUserRoleCommand,
)
from app.database import get_db
from app.form_requests.admin import UpdateUserRoleRequest
from app.models import User
from app.schemas import UpdateUserRoleIn, UserAdminOut

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get(
    "/users",
    response_model=list[UserAdminOut],
    summary="Список пользователей",
    description="Доступно только пользователю с ролью `admin`.",
)
def list_users(
    _admin: Annotated[User, Depends(admin_required)],
    db: Annotated[Session, Depends(get_db)],
) -> list[UserAdminOut]:
    return dispatch_query(ListUsersQuery(db=db), list[UserAdminOut])


@router.put(
    "/users/{user_id}/role",
    response_model=UserAdminOut,
    summary="Сменить роль пользователя",
    description=(
        "Назначает роль `admin`, `ezh` или `kot`. "
        "Нельзя изменить свою роль. Требуется сессия admin и заголовок `X-CSRF-Token`."
    ),
)
def update_user_role(
    user_id: int,
    body: UpdateUserRoleIn,
    admin: Annotated[User, Depends(admin_required)],
    db: Annotated[Session, Depends(get_db)],
) -> UserAdminOut:
    form = UpdateUserRoleRequest.from_body(body)
    return dispatch_command(
        UpdateUserRoleCommand(db=db, actor=admin, target_user_id=user_id, form=form),
        UserAdminOut,
    )


@router.get(
    "/users/{user_id}/protocol-draft.pdf",
    summary="Черновик протокола пользователя",
    description=(
        "PDF-черновик из профиля выбранного пользователя. "
        "Доступно только admin; профиль экзаменуемого должен быть заполнен."
    ),
)
def download_user_protocol_draft(
    user_id: int,
    admin: Annotated[User, Depends(admin_required)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    pdf_bytes = dispatch_query(
        GetUserProtocolDraftPdfQuery(db=db, actor=admin, target_user_id=user_id),
        bytes,
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="protocol_draft_user_{user_id}.pdf"'
        },
    )
