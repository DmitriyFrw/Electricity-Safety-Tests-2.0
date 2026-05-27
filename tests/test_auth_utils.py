from __future__ import annotations

from app.auth_utils import hash_password, verify_password


def test_password_hash_and_verify():
    plain = "my-secure-password"
    hashed = hash_password(plain)
    assert hashed != plain
    assert hashed.startswith("$2")
    assert verify_password(plain, hashed)
    assert not verify_password("wrong-password", hashed)


def test_password_hashes_differ_for_same_input():
    a = hash_password("same-password")
    b = hash_password("same-password")
    assert a != b  # bcrypt salt
