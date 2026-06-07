from app.support.rich_text import sanitize_wiki_rich_text


def test_sanitize_wiki_allows_safe_link():
    raw = '<p>Текст <a href="https://example.com">ссылка</a></p>'
    cleaned = sanitize_wiki_rich_text(raw)
    assert 'href="https://example.com"' in cleaned
    assert "ссылка" in cleaned


def test_sanitize_wiki_allows_wiki_attachment_image():
    raw = '<p><img src="/api/wiki/attachments/5" alt="photo"></p>'
    cleaned = sanitize_wiki_rich_text(raw)
    assert 'src="/api/wiki/attachments/5"' in cleaned


def test_sanitize_wiki_strips_unsafe_link():
    raw = '<a href="javascript:alert(1)">x</a>'
    cleaned = sanitize_wiki_rich_text(raw)
    assert "javascript:" not in cleaned
