from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import staff_required
from app.cqrs.bus import dispatch_command, dispatch_query
from app.cqrs.messages.staff import ListKotUsersQuery, UpdateKotSafetyGroupCommand
from app.database import get_db
from app.models import User
from app.schemas import KotUserOut, UpdateKotSafetyGroupIn

router = APIRouter(prefix="/staff", tags=["staff"])


@router.get(
    "/kot-users",
    response_model=list[KotUserOut],
    summary="Список пользователей Кот",
    description="Доступно ролям admin и Еж для управления группами по электробезопасности.",
)
def list_kot_users(
    actor: Annotated[User, Depends(staff_required)],
    db: Annotated[Session, Depends(get_db)],
) -> list[KotUserOut]:
    return dispatch_query(ListKotUsersQuery(db=db, actor=actor), list[KotUserOut])


@router.put(
    "/kot-users/{user_id}/safety-group",
    response_model=KotUserOut,
    summary="Назначить группу по ЭБ пользователю Кот",
    description="Доступно ролям admin и Еж. Допустимые значения: I, II, III, IV.",
)
def update_kot_safety_group(
    user_id: int,
    body: UpdateKotSafetyGroupIn,
    actor: Annotated[User, Depends(staff_required)],
    db: Annotated[Session, Depends(get_db)],
) -> KotUserOut:
    return dispatch_command(
        UpdateKotSafetyGroupCommand(
            db=db, actor=actor, target_user_id=user_id, form=body
        ),
        KotUserOut,
    )
