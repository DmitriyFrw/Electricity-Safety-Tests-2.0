from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from app.api.deps import login_required, wiki_editor_required
from app.cqrs.bus import dispatch_command, dispatch_query
from app.cqrs.handlers.wiki import save_wiki_attachment
from app.cqrs.messages.wiki import (
    CreateWikiPageCommand,
    DeleteWikiAttachmentCommand,
    DeleteWikiPageCommand,
    GetWikiAttachmentPathQuery,
    GetWikiPageQuery,
    ListWikiPagesQuery,
    UpdateWikiPageCommand,
)
from app.database import get_db
from app.models import User
from app.schemas import WikiAttachmentOut, WikiPageCreateIn, WikiPageListItemOut, WikiPageOut, WikiPageUpdateIn

router = APIRouter(prefix="/wiki", tags=["wiki"])


@router.get("/pages", response_model=list[WikiPageListItemOut])
def list_wiki_pages(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
) -> list[WikiPageListItemOut]:
    return dispatch_query(ListWikiPagesQuery(db=db, user=user), list[WikiPageListItemOut])


@router.get("/pages/{page_id}", response_model=WikiPageOut)
def get_wiki_page(
    page_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
) -> WikiPageOut:
    return dispatch_query(GetWikiPageQuery(db=db, user=user, page_id=page_id), WikiPageOut)


@router.post("/pages", response_model=WikiPageOut, status_code=201)
def create_wiki_page(
    body: WikiPageCreateIn,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(wiki_editor_required)],
) -> WikiPageOut:
    return dispatch_command(
        CreateWikiPageCommand(db=db, user=user, title=body.title, content=body.content),
        WikiPageOut,
    )


@router.put("/pages/{page_id}", response_model=WikiPageOut)
def update_wiki_page(
    page_id: int,
    body: WikiPageUpdateIn,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(wiki_editor_required)],
) -> WikiPageOut:
    return dispatch_command(
        UpdateWikiPageCommand(
            db=db,
            user=user,
            page_id=page_id,
            title=body.title,
            content=body.content,
        ),
        WikiPageOut,
    )


@router.delete("/pages/{page_id}", status_code=204)
def delete_wiki_page(
    page_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(wiki_editor_required)],
) -> Response:
    dispatch_command(DeleteWikiPageCommand(db=db, user=user, page_id=page_id), type(None))
    return Response(status_code=204)


@router.post("/pages/{page_id}/attachments", response_model=WikiAttachmentOut, status_code=201)
async def upload_wiki_attachment(
    page_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(wiki_editor_required)],
    file: UploadFile = File(...),
) -> WikiAttachmentOut:
    data = await file.read()
    return save_wiki_attachment(
        db,
        user=user,
        page_id=page_id,
        filename=file.filename or "file",
        mime_type=file.content_type or "application/octet-stream",
        data=data,
    )


@router.delete("/attachments/{attachment_id}", response_model=WikiPageOut)
def delete_wiki_attachment(
    attachment_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(wiki_editor_required)],
) -> WikiPageOut:
    return dispatch_command(
        DeleteWikiAttachmentCommand(db=db, user=user, attachment_id=attachment_id),
        WikiPageOut,
    )


@router.get("/attachments/{attachment_id}")
def download_wiki_attachment(
    attachment_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
) -> FileResponse:
    result = dispatch_query(
        GetWikiAttachmentPathQuery(db=db, user=user, attachment_id=attachment_id),
        tuple,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Файл не найден")
    path, filename, mime_type = result
    return FileResponse(path, media_type=mime_type, filename=filename)
