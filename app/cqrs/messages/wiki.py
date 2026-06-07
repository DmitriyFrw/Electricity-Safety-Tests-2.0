from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models import User


@dataclass(frozen=True)
class ListWikiPagesQuery:
    db: Session
    user: User


@dataclass(frozen=True)
class GetWikiPageQuery:
    db: Session
    user: User
    page_id: int


@dataclass(frozen=True)
class CreateWikiPageCommand:
    db: Session
    user: User
    title: str
    content: str


@dataclass(frozen=True)
class UpdateWikiPageCommand:
    db: Session
    user: User
    page_id: int
    title: str
    content: str


@dataclass(frozen=True)
class DeleteWikiPageCommand:
    db: Session
    user: User
    page_id: int


@dataclass(frozen=True)
class DeleteWikiAttachmentCommand:
    db: Session
    user: User
    attachment_id: int


@dataclass(frozen=True)
class GetWikiAttachmentPathQuery:
    db: Session
    user: User
    attachment_id: int
