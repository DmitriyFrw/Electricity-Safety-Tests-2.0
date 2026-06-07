from __future__ import annotations

import re
import shutil
import uuid
from pathlib import Path

from sqlalchemy import func, select

from app.cqrs.messages.wiki import (
    CreateWikiPageCommand,
    DeleteWikiAttachmentCommand,
    DeleteWikiPageCommand,
    GetWikiAttachmentPathQuery,
    GetWikiPageQuery,
    ListWikiPagesQuery,
    UpdateWikiPageCommand,
)
from app.models import WikiAttachment, WikiPage
from app.policies import AccessPolicy
from app.schemas import WikiAttachmentOut, WikiPageListItemOut, WikiPageOut
from app.support.errors import AppError
from app.support.rich_text import plain_text_from_rich, sanitize_wiki_rich_text

WIKI_UPLOADS_DIR = Path(__file__).resolve().parent.parent.parent / "static" / "wiki"
MAX_WIKI_ATTACHMENT_BYTES = 10 * 1024 * 1024
IMAGE_MIME_PREFIX = "image/"


def _require_wiki_editor(user) -> None:
    if not AccessPolicy.can_edit_wiki(user):
        raise AppError("Редактирование вики доступно только ролям admin и Еж", status_code=403)


def _attachment_out(att: WikiAttachment) -> WikiAttachmentOut:
    url = f"/api/wiki/attachments/{att.id}"
    return WikiAttachmentOut(
        id=att.id,
        filename=att.filename,
        mime_type=att.mime_type,
        size_bytes=att.size_bytes,
        url=url,
        is_image=att.mime_type.startswith(IMAGE_MIME_PREFIX),
    )


def _page_out(page: WikiPage) -> WikiPageOut:
    return WikiPageOut(
        id=page.id,
        title=page.title,
        content=page.content,
        updated_at=page.updated_at,
        attachments=[_attachment_out(a) for a in page.attachments],
    )


def _page_dir(page_id: int) -> Path:
    return WIKI_UPLOADS_DIR / str(page_id)


def _safe_stored_name(original: str) -> str:
    ext = Path(original).suffix.lower()
    if ext and not re.fullmatch(r"\.[a-z0-9]{1,8}", ext):
        ext = ""
    return f"{uuid.uuid4().hex}{ext}"


class ListWikiPagesHandler:
    def handle(self, query: ListWikiPagesQuery) -> list[WikiPageListItemOut]:
        pages = (
            query.db.execute(
                select(WikiPage).order_by(WikiPage.position.asc(), WikiPage.id.asc())
            )
            .scalars()
            .all()
        )
        return [
            WikiPageListItemOut(id=p.id, title=p.title, updated_at=p.updated_at) for p in pages
        ]


class GetWikiPageHandler:
    def handle(self, query: GetWikiPageQuery) -> WikiPageOut:
        page = query.db.get(WikiPage, query.page_id)
        if page is None:
            raise AppError("Страница не найдена", status_code=404)
        return _page_out(page)


class CreateWikiPageHandler:
    def handle(self, command: CreateWikiPageCommand) -> WikiPageOut:
        _require_wiki_editor(command.user)
        title = command.title.strip()
        if not title:
            raise AppError("Укажите название страницы", status_code=400)
        content = sanitize_wiki_rich_text(command.content)
        if not plain_text_from_rich(content) and "<img" not in content.lower():
            pass  # empty content allowed on create
        max_pos = command.db.scalar(select(func.max(WikiPage.position))) or 0
        page = WikiPage(
            title=title[:200],
            content=content,
            position=max_pos + 1,
            updated_by_id=command.user.id,
        )
        command.db.add(page)
        command.db.commit()
        command.db.refresh(page)
        _page_dir(page.id).mkdir(parents=True, exist_ok=True)
        return _page_out(page)


class UpdateWikiPageHandler:
    def handle(self, command: UpdateWikiPageCommand) -> WikiPageOut:
        _require_wiki_editor(command.user)
        page = command.db.get(WikiPage, command.page_id)
        if page is None:
            raise AppError("Страница не найдена", status_code=404)
        title = command.title.strip()
        if not title:
            raise AppError("Укажите название страницы", status_code=400)
        page.title = title[:200]
        page.content = sanitize_wiki_rich_text(command.content)
        page.updated_by_id = command.user.id
        command.db.commit()
        command.db.refresh(page)
        return _page_out(page)


class DeleteWikiPageHandler:
    def handle(self, command: DeleteWikiPageCommand) -> None:
        _require_wiki_editor(command.user)
        page = command.db.get(WikiPage, command.page_id)
        if page is None:
            raise AppError("Страница не найдена", status_code=404)
        page_id = page.id
        command.db.delete(page)
        command.db.commit()
        shutil.rmtree(_page_dir(page_id), ignore_errors=True)


class DeleteWikiAttachmentHandler:
    def handle(self, command: DeleteWikiAttachmentCommand) -> WikiPageOut:
        _require_wiki_editor(command.user)
        att = command.db.get(WikiAttachment, command.attachment_id)
        if att is None:
            raise AppError("Файл не найден", status_code=404)
        page = att.page
        path = _page_dir(att.page_id) / att.stored_name
        command.db.delete(att)
        command.db.commit()
        if path.is_file():
            path.unlink(missing_ok=True)
        command.db.refresh(page)
        return _page_out(page)


class GetWikiAttachmentPathHandler:
    def handle(self, query: GetWikiAttachmentPathQuery) -> tuple[Path, str, str] | None:
        att = query.db.get(WikiAttachment, query.attachment_id)
        if att is None:
            return None
        path = _page_dir(att.page_id) / att.stored_name
        if not path.is_file():
            return None
        return path, att.filename, att.mime_type


def save_wiki_attachment(
    db,
    *,
    user,
    page_id: int,
    filename: str,
    mime_type: str,
    data: bytes,
) -> WikiAttachmentOut:
    _require_wiki_editor(user)
    if len(data) > MAX_WIKI_ATTACHMENT_BYTES:
        raise AppError("Файл слишком большой (максимум 10 МБ)", status_code=400)
    page = db.get(WikiPage, page_id)
    if page is None:
        raise AppError("Страница не найдена", status_code=404)
    safe_name = (filename or "file").strip()[:255] or "file"
    stored = _safe_stored_name(safe_name)
    page_dir = _page_dir(page_id)
    page_dir.mkdir(parents=True, exist_ok=True)
    dest = page_dir / stored
    dest.write_bytes(data)
    att = WikiAttachment(
        page_id=page_id,
        filename=safe_name,
        stored_name=stored,
        mime_type=mime_type or "application/octet-stream",
        size_bytes=len(data),
    )
    db.add(att)
    page.updated_by_id = user.id
    db.commit()
    db.refresh(att)
    return _attachment_out(att)
