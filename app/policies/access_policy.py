from __future__ import annotations

from app.constants import ROLE_ADMIN, ROLE_EZH, ROLE_KOT
from app.models import Test, User


class AccessPolicy:
    @staticmethod
    def can_create_tests(user: User) -> bool:
        return user.role in {ROLE_ADMIN, ROLE_EZH}

    @staticmethod
    def can_edit_test(user: User, test: Test) -> bool:
        return user.role == ROLE_ADMIN or (user.role == ROLE_EZH and test.author_id == user.id)

    @staticmethod
    def can_manage_profile_pdf(user: User) -> bool:
        return user.role == ROLE_KOT

    @staticmethod
    def can_manage_users(user: User) -> bool:
        return user.role == ROLE_ADMIN

    @staticmethod
    def can_export_user_protocol_draft(user: User) -> bool:
        return user.role == ROLE_ADMIN

    @staticmethod
    def can_manage_safety_groups(user: User) -> bool:
        return user.role in {ROLE_ADMIN, ROLE_EZH}

    @staticmethod
    def can_edit_wiki(user: User) -> bool:
        return user.role in {ROLE_ADMIN, ROLE_EZH}
