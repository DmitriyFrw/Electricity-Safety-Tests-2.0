from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import User


class UserRepository:
    @staticmethod
    def get_by_username(db: Session, username: str) -> User | None:
        return db.query(User).filter(User.username == username).one_or_none()

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> User | None:
        return db.get(User, user_id)

    @staticmethod
    def list_all(db: Session) -> list[User]:
        return db.query(User).order_by(User.username).all()
