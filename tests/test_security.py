from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from app.config import Settings
from app.cqrs.handlers.manuals import _resolve_manual_path
from app.services.security.login_rate_limiter import LoginRateLimiter
from app.support.file_types import validate_wiki_upload
from app.support.rich_text import (
    WIKI_ALLOWED_ATTRS,
    WIKI_ALLOWED_TAGS,
    plain_text_from_rich,
    sanitize_wiki_rich_text,
)


def test_production_rejects_default_secret_key():
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(
            database_url="postgresql+psycopg://u:p@localhost/db",
            secret_key="dev-change-me-in-production",
            session_cookie_secure=True,
            auto_create_schema=False,
        )


def test_production_accepts_strong_secret_key():
    settings = Settings(
        database_url="postgresql+psycopg://u:p@localhost/db",
        secret_key="x" * 32,
        session_cookie_secure=True,
        auto_create_schema=False,
    )
    assert settings.is_production is True


def test_manual_path_rejects_traversal():
    assert _resolve_manual_path("../etc/passwd") is None
    assert _resolve_manual_path("..") is None
    assert _resolve_manual_path("foo/bar") is None


def test_validate_wiki_upload_rejects_svg_and_html():
    svg = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
    html = b"<!doctype html><html><body>x</body></html>"
    with pytest.raises(ValueError, match="Недопустимый"):
        validate_wiki_upload("icon.svg", svg)
    with pytest.raises(ValueError, match="Недопустимый"):
        validate_wiki_upload("page.html", html)
    with pytest.raises(ValueError, match="Недопустимый"):
        validate_wiki_upload("fake.png", svg)


@pytest.mark.parametrize("tag", WIKI_ALLOWED_TAGS)
def test_wiki_sanitizer_keeps_allowed_tags(tag: str):
    if tag == "br":
        raw = "до<br>после"
        assert "<br" in sanitize_wiki_rich_text(raw)
        return
    if tag == "img":
        raw = '<img src="/api/wiki/attachments/1" alt="x">'
        cleaned = sanitize_wiki_rich_text(raw)
        assert "<img" in cleaned
        assert "/api/wiki/attachments/1" in cleaned
        return
    if tag == "a":
        raw = '<a href="https://example.com" target="_blank" rel="noopener">link</a>'
        cleaned = sanitize_wiki_rich_text(raw)
        assert "<a" in cleaned
        assert 'href="https://example.com"' in cleaned
        return
    raw = f"<{tag}>текст</{tag}>"
    cleaned = sanitize_wiki_rich_text(raw)
    assert f"<{tag}" in cleaned


def test_wiki_sanitizer_strips_script_and_onclick():
    raw = '<p onclick="alert(1)">x</p><script>alert(1)</script><b>ok</b>'
    cleaned = sanitize_wiki_rich_text(raw)
    assert "script" not in cleaned.lower()
    assert "onclick" not in cleaned.lower()
    assert "<b>ok</b>" in cleaned


def test_wiki_sanitizer_blocks_external_images():
    cleaned = sanitize_wiki_rich_text('<img src="https://evil.example/x.png" alt="x">')
    assert "evil.example" not in cleaned


def test_wiki_allowed_attrs_documented():
    link = sanitize_wiki_rich_text(
        '<a href="https://example.com" target="_blank" rel="noopener" style="color: red">x</a>'
    )
    assert 'href="https://example.com"' in link
    assert 'target="_blank"' in link
    assert 'rel="noopener"' in link
    assert "color" in link

    image = sanitize_wiki_rich_text(
        '<img src="/api/wiki/attachments/42" alt="pic" style="max-width: 100%">'
    )
    assert 'src="/api/wiki/attachments/42"' in image
    assert 'alt="pic"' in image

    block = sanitize_wiki_rich_text('<p style="text-align: center">центр</p>')
    assert "text-align: center" in block


def test_plain_text_from_rich_strips_wiki_markup():
    assert plain_text_from_rich('<p><a href="https://x">Link</a></p>') == "Link"


def test_login_rate_limiter_uses_redis_when_configured():
    LoginRateLimiter._redis = None
    mock_client = MagicMock()
    mock_client.get.return_value = "2"
    mock_client.incr.return_value = 3

    with patch("app.services.security.login_rate_limiter.get_settings") as settings:
        settings.return_value.redis_url = "redis://localhost:6379/0"
        settings.return_value.login_rate_limit_attempts = 5
        settings.return_value.login_rate_limit_window_seconds = 300
        with patch("redis.from_url", return_value=mock_client):
            LoginRateLimiter._redis = None
            assert LoginRateLimiter.is_blocked(username="u", ip="1.2.3.4") is False
            count = LoginRateLimiter.register_failure(username="u", ip="1.2.3.4")
            assert count == 3
            LoginRateLimiter.reset(username="u", ip="1.2.3.4")
            mock_client.delete.assert_called_once()

    LoginRateLimiter._redis = None
