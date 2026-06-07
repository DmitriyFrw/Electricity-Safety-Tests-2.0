from __future__ import annotations

from app.constants import ROLE_ADMIN, ROLE_EZH, ROLES_CAN_EDIT_TESTS
from app.models import Test, User
from app.policies import AccessPolicy


def role_label(role: str) -> str:
    from app.constants import ROLE_LABELS

    return ROLE_LABELS.get(role, role)


def can_create_tests(user: User) -> bool:
    return AccessPolicy.can_create_tests(user)


def can_edit_test(user: User, test: Test) -> bool:
    return AccessPolicy.can_edit_test(user, test)


def can_edit_wiki(user: User) -> bool:
    return AccessPolicy.can_edit_wiki(user)


def is_kot(user: User) -> bool:
    from app.constants import ROLE_KOT

    return user.role == ROLE_KOT
