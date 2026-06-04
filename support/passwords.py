from __future__ import annotations

from functools import lru_cache

from passlib.context import CryptContext

from app.config import get_settings


@lru_cache
def _pwd_context() -> CryptContext:
    return CryptContext(
        schemes=["bcrypt"],
        deprecated="auto",
        bcrypt__rounds=get_settings().bcrypt_rounds,
    )


def hash_password(password: str) -> str:
    return _pwd_context().hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context().verify(plain, hashed)
