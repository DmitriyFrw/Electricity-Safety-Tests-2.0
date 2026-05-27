from __future__ import annotations

from app.constants import ROLE_ADMIN, ROLE_EZH, ROLES_CAN_EDIT_TESTS
from app.models import Test, User


def role_label(role: str) -> str:
    from app.constants import ROLE_LABELS

    return ROLE_LABELS.get(role, role)


def can_create_tests(user: User) -> bool:
    return user.role in ROLES_CAN_EDIT_TESTS


def can_edit_test(user: User, test: Test) -> bool:
    if user.role == ROLE_ADMIN:
        return True
    if user.role == ROLE_EZH and test.author_id == user.id:
        return True
    return False


def is_kot(user: User) -> bool:
    from app.constants import ROLE_KOT

    return user.role == ROLE_KOT
