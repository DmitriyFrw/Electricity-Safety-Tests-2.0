from __future__ import annotations

import datetime as dt
import logging
from io import BytesIO
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from app.models import User

TEMPLATE_DIR = Path(__file__).resolve().parent / "static" / "templates"
TEMPLATE_PATH = TEMPLATE_DIR / "protocol_template.pdf"
FONTS_DIR = Path(__file__).resolve().parent / "static" / "fonts"
logger = logging.getLogger("pdf-service")

# Координаты полей на шаблоне (A4, pt, origin bottom-left)
FIELD_POSITIONS = {
    "full_name": (120, 620),
    "birth_date": (120, 590),
    "job_title": (120, 560),
    "generated_at": (120, 530),
}


def _ensure_template() -> Path:
    TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    if TEMPLATE_PATH.exists():
        return TEMPLATE_PATH

    c = canvas.Canvas(str(TEMPLATE_PATH), pagesize=A4)
    width, height = A4
    font_regular, font_bold, font_italic = _resolve_fonts()
    c.setFont(font_bold, 16)
    c.drawCentredString(width / 2, height - 80, "Протокол проверки знаний")
    c.setFont(font_regular, 12)
    c.drawString(72, height - 130, "По электробезопасности")
    c.setFont(font_regular, 11)
    c.drawString(72, 620, "ФИО:")
    c.drawString(72, 590, "Дата рождения:")
    c.drawString(72, 560, "Занимаемая должность:")
    c.drawString(72, 530, "Дата формирования:")
    c.line(200, 615, width - 72, 615)
    c.line(200, 585, width - 72, 585)
    c.line(200, 555, width - 72, 555)
    c.line(200, 525, width - 72, 525)
    c.setFont(font_italic, 9)
    c.drawString(72, 80, "Документ сформирован автоматически из личного кабинета платформы «Развивайся».")
    c.save()
    return TEMPLATE_PATH


def _resolve_fonts() -> tuple[str, str, str]:
    """Возвращает имена зарегистрированных шрифтов с поддержкой кириллицы."""
    regular_candidates = [
        FONTS_DIR / "DejaVuSans.ttf",
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/Library/Fonts/Arial Unicode.ttf"),
    ]
    bold_candidates = [
        FONTS_DIR / "DejaVuSans-Bold.ttf",
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ]
    italic_candidates = [
        FONTS_DIR / "DejaVuSans-Oblique.ttf",
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf"),
    ]

    reg_name = _register_font("DejaVuSans", regular_candidates) or "Helvetica"
    bold_name = _register_font("DejaVuSans-Bold", bold_candidates) or "Helvetica-Bold"
    italic_name = _register_font("DejaVuSans-Oblique", italic_candidates) or "Helvetica-Oblique"
    return reg_name, bold_name, italic_name


def _register_font(name: str, candidates: list[Path]) -> str | None:
    if name in pdfmetrics.getRegisteredFontNames():
        return name
    for path in candidates:
        if path.is_file():
            pdfmetrics.registerFont(TTFont(name, str(path)))
            return name
    logger.warning("Cyrillic font %s not found, falling back", name)
    return None


def _format_birth_date(value: dt.date | None) -> str:
    if not value:
        return "—"
    return value.strftime("%d.%m.%Y")


def build_protocol_pdf(user: User) -> bytes:
    """Подставляет данные пользователя в предзагруженный шаблон PDF."""
    _ensure_template()

    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError as e:
        raise RuntimeError("Установите pypdf для формирования PDF") from e

    overlay_buffer = BytesIO()
    c = canvas.Canvas(overlay_buffer, pagesize=A4)
    font_regular, _font_bold, _font_italic = _resolve_fonts()
    c.setFont(font_regular, 11)

    full_name = (user.full_name or user.username or "—").strip()
    birth = _format_birth_date(user.birth_date)
    job = (user.job_title or "—").strip()
    generated = dt.datetime.now(dt.timezone.utc).strftime("%d.%m.%Y %H:%M UTC")

    for key, value in (
        ("full_name", full_name),
        ("birth_date", birth),
        ("job_title", job),
        ("generated_at", generated),
    ):
        x, y = FIELD_POSITIONS[key]
        c.drawString(x, y, value)

    c.save()
    overlay_buffer.seek(0)

    template_reader = PdfReader(str(TEMPLATE_PATH))
    overlay_reader = PdfReader(overlay_buffer)
    writer = PdfWriter()

    base_page = template_reader.pages[0]
    base_page.merge_page(overlay_reader.pages[0])
    writer.add_page(base_page)

    out = BytesIO()
    writer.write(out)
    return out.getvalue()


def build_signed_protocol_pdf(protocol) -> bytes:
    """Формирует финальный подписанный протокол экзамена."""
    out = BytesIO()
    c = canvas.Canvas(out, pagesize=A4)
    width, height = A4
    font_regular, font_bold, _ = _resolve_fonts()
    c.setFont(font_bold, 16)
    c.drawCentredString(width / 2, height - 80, "Подписанный протокол экзамена")

    c.setFont(font_regular, 11)
    y = height - 130
    lines = [
        f"Экзамен: {protocol.test_title}",
        f"Экзаменуемый: {protocol.examinee_full_name}",
        f"Дата рождения: {protocol.examinee_birth_date.strftime('%d.%m.%Y')}",
        f"Должность: {protocol.examinee_job_title}",
        f"Результат: {protocol.result_percent}%",
        f"Подписал: {protocol.signer.username if protocol.signer else protocol.signer_id}",
        f"Дата подписи: {protocol.signed_at.strftime('%d.%m.%Y %H:%M UTC')}",
    ]
    for line in lines:
        c.drawString(72, y, line)
        y -= 26

    c.setFont(font_regular, 9)
    c.drawString(72, 80, "Документ сформирован системой «Развивайся».")
    c.save()
    return out.getvalue()
