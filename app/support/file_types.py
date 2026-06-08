from __future__ import annotations

from pathlib import Path

EXTENSION_MIME: dict[str, str] = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".pdf": "application/pdf",
    ".txt": "text/plain",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

BLOCKED_WIKI_EXTENSIONS = frozenset({".svg", ".html", ".htm", ".xhtml", ".xml", ".js", ".css"})
BLOCKED_WIKI_MIME_PREFIXES = ("image/svg", "text/html", "application/xhtml")
ALLOWED_WIKI_EXTENSIONS = frozenset(EXTENSION_MIME)


def sniff_mime_type(data: bytes) -> str | None:
    if not data:
        return None
    head = data.lstrip()[:512]
    lower = head.lower()
    if lower.startswith((b"<!doctype html", b"<html", b"<?xml", b"<svg")):
        if lower.startswith(b"<svg") or b"<svg" in lower[:256]:
            return "image/svg+xml"
        if lower.startswith((b"<!doctype html", b"<html")):
            return "text/html"
        if lower.startswith(b"<?xml"):
            return "application/xml"
    if data.startswith(b"%PDF"):
        return "application/pdf"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if data[:2] == b"PK":
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    sample = data[:4096]
    if sample and not any(b < 9 and b not in (9, 10, 13) for b in sample):
        try:
            sample.decode("utf-8")
            return "text/plain"
        except UnicodeDecodeError:
            pass
    return None


def is_blocked_wiki_mime(mime: str) -> bool:
    lower = mime.lower()
    return any(lower.startswith(prefix) for prefix in BLOCKED_WIKI_MIME_PREFIXES)


def validate_wiki_upload(filename: str, data: bytes) -> str:
    """Проверяет расширение и MIME по содержимому; возвращает доверенный MIME."""
    ext = Path(filename or "file").suffix.lower()
    if ext in BLOCKED_WIKI_EXTENSIONS:
        raise ValueError("Недопустимый тип файла")
    if ext not in ALLOWED_WIKI_EXTENSIONS:
        raise ValueError("Недопустимый тип файла")
    expected = EXTENSION_MIME[ext]
    sniffed = sniff_mime_type(data)
    if sniffed is None:
        raise ValueError("Не удалось определить тип файла")
    if is_blocked_wiki_mime(sniffed):
        raise ValueError("Недопустимый тип файла")
    if sniffed != expected:
        raise ValueError("Содержимое файла не соответствует расширению")
    return expected
