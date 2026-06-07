from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.auth_utils import hash_password
from app.database import SessionLocal
from app.models import User
from app.main import app
from tests.conftest import get_csrf_token


@pytest.mark.asyncio
async def test_wiki_kot_can_read_admin_can_edit(async_client: AsyncClient):
    db = SessionLocal()
    try:
        admin = User(username="wiki_admin", password_hash=hash_password("password123"), role="admin")
        db.add(admin)
        db.commit()
        db.refresh(admin)
        admin_id = admin.id
    finally:
        db.close()

    csrf = await get_csrf_token(async_client)
    login = await async_client.post(
        "/api/auth/login",
        json={"username": "wiki_admin", "password": "password123"},
        headers={"X-CSRF-Token": csrf},
    )
    assert login.status_code == 200
    assert login.json()["can_edit_wiki"] is True

    csrf = await get_csrf_token(async_client)
    create = await async_client.post(
        "/api/wiki/pages",
        json={"title": "Правила портала", "content": "<p>Описание</p>"},
        headers={"X-CSRF-Token": csrf},
    )
    assert create.status_code == 201
    page_id = create.json()["id"]

    list_r = await async_client.get("/api/wiki/pages")
    assert list_r.status_code == 200
    assert len(list_r.json()) == 1

    get_r = await async_client.get(f"/api/wiki/pages/{page_id}")
    assert get_r.status_code == 200
    assert get_r.json()["title"] == "Правила портала"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as kot_client:
        kot_csrf = await get_csrf_token(kot_client)
        reg = await kot_client.post(
            "/api/auth/register",
            json={"username": "wiki_kot", "password": "password123", "password2": "password123"},
            headers={"X-CSRF-Token": kot_csrf},
        )
        assert reg.status_code == 200
        assert reg.json()["can_edit_wiki"] is False

        kot_list = await kot_client.get("/api/wiki/pages")
        assert kot_list.status_code == 200
        assert kot_list.json()[0]["title"] == "Правила портала"

        kot_csrf = await get_csrf_token(kot_client)
        denied = await kot_client.post(
            "/api/wiki/pages",
            json={"title": "X", "content": ""},
            headers={"X-CSRF-Token": kot_csrf},
        )
        assert denied.status_code == 403

    _ = admin_id
