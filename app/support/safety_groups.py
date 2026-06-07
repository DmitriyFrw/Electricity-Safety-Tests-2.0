from __future__ import annotations

from app.constants import (
    DEFAULT_KOT_SAFETY_GROUP,
    ROLE_ADMIN,
    ROLE_EZH,
    ROLE_KOT,
    SAFETY_GROUP_DESCRIPTIONS,
    SAFETY_GROUPS,
)
from app.models import User
from app.support.errors import AppError


def is_valid_safety_group(value: str | None) -> bool:
    return value in SAFETY_GROUPS


def safety_group_label(group: str) -> str:
    if group in SAFETY_GROUPS:
        return f"{group} группа"
    return group


def safety_group_description(group: str) -> str:
    return safety_group_label(group)


def effective_safety_group(user: User) -> str:
    if user.safety_group and is_valid_safety_group(user.safety_group):
        return user.safety_group
    if user.role == ROLE_KOT:
        return DEFAULT_KOT_SAFETY_GROUP
    return DEFAULT_KOT_SAFETY_GROUP


def can_manage_safety_groups(actor: User) -> bool:
    return actor.role in {ROLE_ADMIN, ROLE_EZH}


def require_can_manage_safety_groups(actor: User) -> None:
    if not can_manage_safety_groups(actor):
        raise AppError(
            "Изменение группы по электробезопасности доступно ролям admin и Еж",
            status_code=403,
        )


def validate_safety_group_value(value: str) -> str:
    g = value.strip().upper()
    if not is_valid_safety_group(g):
        raise AppError(
            f"Укажите группу: {', '.join(SAFETY_GROUPS)}",
            status_code=400,
        )
    return g
