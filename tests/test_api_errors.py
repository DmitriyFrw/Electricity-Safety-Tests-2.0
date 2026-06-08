from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_api_error_format_includes_code_and_correlation_id():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/auth/register",
            json={"username": "x", "password": "short", "password2": "short"},
        )
    assert r.status_code == 403
    body = r.json()
    assert "detail" in body
    assert body.get("code") == "csrf_invalid"
    assert body.get("correlation_id")
    assert r.headers.get("X-Correlation-ID")
