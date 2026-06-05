from __future__ import annotations

import re

import bleach
from bleach.css_sanitizer import CSSSanitizer

_ALLOWED_TAGS = [
    "b",
    "strong",
    "i",
    "em",
    "u",
    "s",
    "strike",
    "sub",
    "sup",
    "span",
    "br",
    "ol",
    "ul",
    "li",
    "p",
    "div",
    "h3",
    "h4",
]
_ALLOWED_ATTRS = {
    "span": ["style"],
    "p": ["style"],
    "div": ["style"],
    "h3": ["style"],
    "h4": ["style"],
}
_CSS = CSSSanitizer(
    allowed_css_properties=[
        "color",
        "background-color",
        "font-size",
        "font-family",
        "text-decoration",
        "font-weight",
        "font-style",
        "text-align",
    ]
)


def sanitize_rich_text(value: str) -> str:
    """Оставляет безопасное HTML-оформление для текста билетов."""
    raw = (value or "").strip()
    if not raw:
        return ""
    if "<" not in raw:
        return raw
    raw = re.sub(r"<script\b[^>]*>.*?</script>", "", raw, flags=re.IGNORECASE | re.DOTALL)
    return bleach.clean(
        raw,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRS,
        css_sanitizer=_CSS,
        strip=True,
    )


def plain_text_from_rich(value: str) -> str:
    """Текст без разметки — для проверки «заполнено ли поле»."""
    if not value:
        return ""
    cleaned = bleach.clean(value or "", tags=[], strip=True)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()
