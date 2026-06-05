from app.support.rich_text import plain_text_from_rich, sanitize_rich_text


def test_sanitize_strips_script():
    raw = '<script>alert(1)</script><b>Текст</b>'
    assert sanitize_rich_text(raw) == "<b>Текст</b>"


def test_plain_text_from_rich_ignores_tags():
    assert plain_text_from_rich("<b>Ответ</b>") == "Ответ"


def test_sanitize_allows_lists_and_alignment():
    raw = '<p style="text-align: center"><b>Текст</b></p><ul><li>пункт</li></ul>'
    cleaned = sanitize_rich_text(raw)
    assert "text-align: center" in cleaned
    assert "<ul>" in cleaned
    assert "<li>" in cleaned
