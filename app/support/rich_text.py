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

_WIKI_EXTRA_TAGS = ["a", "img"]

_ALLOWED_ATTRS = {
    "span": ["style"],
    "p": ["style"],
    "div": ["style"],
    "h3": ["style"],
    "h4": ["style"],
}

_WIKI_EXTRA_ATTRS = {
    "a": ["href", "target", "rel", "style"],
    "img": ["src", "alt", "style"],
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
    return _sanitize_html(value, tags=_ALLOWED_TAGS, attrs=_ALLOWED_ATTRS)


def _is_safe_link_url(url: str) -> bool:
    u = (url or "").strip()
    if not u:
        return False
    if u.startswith("/api/wiki/attachments/"):
        return True
    lower = u.lower()
    return lower.startswith("http://") or lower.startswith("https://")


def _is_safe_image_src(src: str) -> bool:
    return (src or "").strip().startswith("/api/wiki/attachments/")


def sanitize_wiki_rich_text(value: str) -> str:
    """HTML для страниц вики: ссылки и изображения вложений."""
    tags = _ALLOWED_TAGS + _WIKI_EXTRA_TAGS
    allowed = {**_ALLOWED_ATTRS, **_WIKI_EXTRA_ATTRS}

    def wiki_attributes(tag: str, name: str, value: str) -> bool:
        if tag == "a" and name == "href":
            return _is_safe_link_url(value)
        if tag == "img" and name == "src":
            return _is_safe_image_src(value)
        return tag in allowed and name in allowed.get(tag, [])

    raw = (value or "").strip()
    if not raw:
        return ""
    if "<" not in raw:
        return raw
    raw = re.sub(r"<script\b[^>]*>.*?</script>", "", raw, flags=re.IGNORECASE | re.DOTALL)
    return bleach.clean(
        raw,
        tags=tags,
        attributes=wiki_attributes,
        css_sanitizer=_CSS,
        strip=True,
    )


def _sanitize_html(value: str, *, tags: list[str], attrs: dict[str, list[str]]) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    if "<" not in raw:
        return raw
    raw = re.sub(r"<script\b[^>]*>.*?</script>", "", raw, flags=re.IGNORECASE | re.DOTALL)
    return bleach.clean(
        raw,
        tags=tags,
        attributes=attrs,
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
