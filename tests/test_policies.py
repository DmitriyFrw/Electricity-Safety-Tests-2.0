from __future__ import annotations

from app.constants import ROLE_ADMIN, ROLE_EZH, ROLE_KOT
from app.models import Test, User
from app.policies import AccessPolicy


def _user(uid: int, role: str) -> User:
    return User(id=uid, username=f"u{uid}", password_hash="x", role=role)


def test_access_policy_create_tests():
    assert AccessPolicy.can_create_tests(_user(1, ROLE_ADMIN))
    assert AccessPolicy.can_create_tests(_user(2, ROLE_EZH))
    assert not AccessPolicy.can_create_tests(_user(3, ROLE_KOT))


def test_access_policy_edit_test():
    owner = _user(10, ROLE_EZH)
    outsider = _user(11, ROLE_EZH)
    admin = _user(12, ROLE_ADMIN)
    test = Test(id=1, author_id=10, title="T", description=None)

    assert AccessPolicy.can_edit_test(owner, test)
    assert AccessPolicy.can_edit_test(admin, test)
    assert not AccessPolicy.can_edit_test(outsider, test)


def test_access_policy_edit_wiki():
    assert AccessPolicy.can_edit_wiki(_user(1, ROLE_ADMIN))
    assert AccessPolicy.can_edit_wiki(_user(2, ROLE_EZH))
    assert not AccessPolicy.can_edit_wiki(_user(3, ROLE_KOT))
