from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from app.models import Attempt, SignedProtocol, Test, User
from app.support.safety_groups import effective_safety_group, safety_group_label
from app.support.exam_history import (
    format_exam_result_line,
    format_protocol_date,
    last_passed_exam_finished_at,
    last_passed_exam_result,
)
from app.services.attempts.scoring import score_attempt
from app.support.grading import grade_for_exam_protocol

_APP_DIR = Path(__file__).resolve().parent.parent.parent
FONTS_DIR = _APP_DIR / "static" / "fonts"
logger = logging.getLogger("pdf-service")

PAGE_MARGIN_X = 56
PAGE_MARGIN_TOP = 42
PAGE_MARGIN_BOTTOM = 48
BODY_SIZE = 9
HINT_SIZE = 7
TITLE_SIZE = 11
HEADER_SIZE = 8
LINE_DROP = 3
VALUE_PAD = 4
LINE_GAP = 15
SECTION_GAP = 20


@dataclass(frozen=True)
class ProtocolFormValues:
    protocol_number: str = ""
    check_date: str = ""
    check_reason: str = ""
    commission_name: str = ""
    chairman: str = ""
    commission_member_1: str = ""
    commission_member_2: str = ""
    regulatory_docs: str = ""
    examinee_name: str = ""
    workplace: str = ""
    position: str = ""
    previous_check_date: str = ""
    exam_grade: str = ""
    safety_group: str = ""
    result_installations: str = ""
    result_labor: str = ""
    result_fire: str = ""
    result_other_1: str = ""
    result_other_2: str = ""


def _resolve_fonts() -> tuple[str, str, str]:
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


def _truncate_to_width(text: str, font_name: str, font_size: float, max_width: float) -> str:
    if not text or pdfmetrics.stringWidth(text, font_name, font_size) <= max_width:
        return text
    ellipsis = "…"
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        chunk = text[:mid] + ellipsis
        if pdfmetrics.stringWidth(chunk, font_name, font_size) <= max_width:
            lo = mid
        else:
            hi = mid - 1
    return ellipsis if lo == 0 else text[:lo] + ellipsis


def _safety_group_for_user(user: User) -> str:
    return safety_group_label(effective_safety_group(user))


class _OfficialProtocolRenderer:
    """Рекомендуемый образец — приложение № 4 к ПОТЭУ (приказ Минтруда № 903н)."""

    _HEADER_LINES = (
        "Приложение № 4",
        "к Правилам по охране труда при эксплуатации",
        "электроустановок, утверждённым приказом Минтруда России",
        "от 15 декабря 2020 г. № 903н",
        "Рекомендуемый образец",
    )

    def __init__(self, buf: BytesIO) -> None:
        self.buf = buf
        self.width, self.height = A4
        self.c = canvas.Canvas(buf, pagesize=A4)
        self.font_regular, self.font_bold, self.font_italic = _resolve_fonts()
        self.line_right = self.width - PAGE_MARGIN_X
        self.y = self.height - PAGE_MARGIN_TOP

    def render(self, values: ProtocolFormValues) -> None:
        self._draw_header_block()
        # Основной текст — ниже блока «Приложение № 4» справа.
        self.y = self.height - PAGE_MARGIN_TOP - 58
        self._draw_title(values.protocol_number)
        self._advance(SECTION_GAP)
        self._draw_commission_section(values)
        self._advance(SECTION_GAP)
        self._draw_examinee_section(values)
        self._advance(SECTION_GAP)
        self._draw_results_section(values)
        self._draw_footer()

    def _draw_header_block(self) -> None:
        self.c.setFont(self.font_regular, HEADER_SIZE)
        x_right = self.line_right
        y = self.height - PAGE_MARGIN_TOP
        for line in self._HEADER_LINES:
            self.c.drawRightString(x_right, y, line)
            y -= 10

    def _draw_title(self, protocol_number: str) -> None:
        self.c.setFont(self.font_bold, TITLE_SIZE)
        center = self.width / 2
        proto = (protocol_number or "").strip()
        title = f"ПРОТОКОЛ № {proto}" if proto else "ПРОТОКОЛ № ______"
        self.c.drawCentredString(center, self.y, title)
        self._advance(16)
        self.c.setFont(self.font_bold, TITLE_SIZE)
        self.c.drawCentredString(
            center,
            self.y,
            "ПРОВЕРКИ ЗНАНИЙ ПРАВИЛ РАБОТЫ В ЭЛЕКТРОУСТАНОВКАХ",
        )

    def _draw_commission_section(self, values: ProtocolFormValues) -> None:
        self._labeled_line("Дата проверки", values.check_date)
        self._labeled_line("Причина проверки", values.check_reason)
        self._labeled_line("Комиссия", values.commission_name, hint="(наименование комиссии)")
        self._advance(4)
        self.c.setFont(self.font_regular, BODY_SIZE)
        self.c.drawString(PAGE_MARGIN_X, self.y, "в составе:")
        self._advance(LINE_GAP)
        self._labeled_line(
            "председатель комиссии",
            values.chairman,
            hint="(должность, фамилия и инициалы)",
        )
        self.c.setFont(self.font_regular, BODY_SIZE)
        self.c.drawString(
            PAGE_MARGIN_X,
            self.y,
            "члены комиссии (должность, фамилия и инициалы):",
        )
        self._advance(LINE_GAP)
        self._full_width_line(values.commission_member_1)
        self._advance(LINE_GAP)
        self._full_width_line(values.commission_member_2)
        self._advance(6)
        self.c.setFont(self.font_regular, BODY_SIZE)
        self.c.drawString(
            PAGE_MARGIN_X,
            self.y,
            "провела проверку знаний нормативных документов, инструкций (указать наименования).",
        )
        self._advance(LINE_GAP)
        self._full_width_line(values.regulatory_docs)

    def _draw_examinee_section(self, values: ProtocolFormValues) -> None:
        self.c.setFont(self.font_bold, BODY_SIZE)
        self.c.drawString(PAGE_MARGIN_X, self.y, "Проверяемый:")
        self._advance(LINE_GAP)
        self.c.setFont(self.font_regular, BODY_SIZE)
        self._labeled_line(
            "фамилия, имя, отчество (при наличии)",
            values.examinee_name,
        )
        self._labeled_line("место работы", values.workplace)
        self._labeled_line("должность", values.position)
        self._labeled_line("дата предыдущей проверки", values.previous_check_date)
        self._labeled_line("оценка", values.exam_grade)
        self._labeled_line("группа по электробезопасности", values.safety_group)

    def _draw_results_section(self, values: ProtocolFormValues) -> None:
        self.c.setFont(self.font_bold, BODY_SIZE)
        self.c.drawString(PAGE_MARGIN_X, self.y, "Результаты проверки знаний:")
        self._advance(LINE_GAP)
        self.c.setFont(self.font_regular, BODY_SIZE)
        self._labeled_line(
            "по устройству электроустановок и технической эксплуатации",
            values.result_installations,
        )
        self._labeled_line("по охране труда", values.result_labor)
        self._labeled_line("по пожарной безопасности", values.result_fire)
        self.c.drawString(
            PAGE_MARGIN_X,
            self.y,
            "других правил и инструкций органов государственного надзора",
        )
        self._advance(LINE_GAP)
        self._full_width_line(values.result_other_1)
        self._advance(LINE_GAP)
        self._full_width_line(values.result_other_2, hint="(наименование правил)")

    def _draw_footer(self) -> None:
        self.c.setFont(self.font_italic, HINT_SIZE)
        self.c.drawString(
            PAGE_MARGIN_X,
            PAGE_MARGIN_BOTTOM,
            "Документ сформирован автоматически из личного кабинета платформы «Развивайся».",
        )

    def _labeled_line(
        self,
        label: str,
        value: str,
        *,
        hint: str | None = None,
    ) -> None:
        self.c.setFont(self.font_regular, BODY_SIZE)
        prefix = f"{label} "
        self.c.drawString(PAGE_MARGIN_X, self.y, prefix)
        label_w = pdfmetrics.stringWidth(prefix, self.font_regular, BODY_SIZE)
        line_x0 = PAGE_MARGIN_X + label_w
        line_y = self.y - LINE_DROP
        self.c.line(line_x0, line_y, self.line_right, line_y)
        text = (value or "").strip()
        if text:
            max_w = self.line_right - line_x0 - VALUE_PAD
            text = _truncate_to_width(text, self.font_regular, BODY_SIZE, max_w)
            self.c.drawString(line_x0 + VALUE_PAD, self.y, text)
        if hint:
            self.c.setFont(self.font_regular, HINT_SIZE)
            mid = (line_x0 + self.line_right) / 2
            self.c.drawCentredString(mid, self.y - 11, hint)
            self._advance(LINE_GAP + 6)
        else:
            self._advance(LINE_GAP)

    def _full_width_line(self, value: str, *, hint: str | None = None) -> None:
        line_y = self.y - LINE_DROP
        self.c.line(PAGE_MARGIN_X, line_y, self.line_right, line_y)
        text = (value or "").strip()
        if text:
            max_w = self.line_right - PAGE_MARGIN_X - VALUE_PAD
            text = _truncate_to_width(text, self.font_regular, BODY_SIZE, max_w)
            self.c.drawString(PAGE_MARGIN_X + VALUE_PAD, self.y, text)
        if hint:
            self.c.setFont(self.font_regular, HINT_SIZE)
            mid = (PAGE_MARGIN_X + self.line_right) / 2
            self.c.drawCentredString(mid, self.y - 11, hint)
            self._advance(LINE_GAP + 6)
        else:
            self._advance(LINE_GAP)

    def _advance(self, dy: float) -> None:
        self.y -= dy


def _render_protocol_pdf(values: ProtocolFormValues) -> bytes:
    buf = BytesIO()
    renderer = _OfficialProtocolRenderer(buf)
    renderer.render(values)
    renderer.c.save()
    return buf.getvalue()


def _workplace_from_business_unit(user: User) -> str:
    return (user.business_unit or "").strip()


def _signed_workplace(protocol: SignedProtocol) -> str:
    examinee = protocol.examinee
    if examinee is not None and examinee.business_unit:
        return examinee.business_unit.strip()
    return ""


def _previous_check_date(db: Session, user_id: int, *, exclude_attempt_id: int | None = None) -> str:
    finished = last_passed_exam_finished_at(
        db, user_id, exclude_attempt_id=exclude_attempt_id
    )
    return format_protocol_date(finished)


def _exam_grade_text(
    db: Session,
    user_id: int,
    *,
    exclude_attempt_id: int | None = None,
    percent: float | None = None,
    grade: str | None = None,
) -> str:
    if grade:
        return grade
    if percent is not None:
        return grade_for_exam_protocol(percent)
    passed = last_passed_exam_result(db, user_id, exclude_attempt_id=exclude_attempt_id)
    return passed.grade if passed else ""


def _installations_exam_result(
    db: Session,
    user_id: int,
    *,
    exclude_attempt_id: int | None = None,
    percent: float | None = None,
    grade: str | None = None,
) -> str:
    """Строка «по устройству электроустановок…» — оценка за экзамен."""
    if percent is not None:
        g = grade or grade_for_exam_protocol(percent)
        return format_exam_result_line(grade=g, percent=percent)
    passed = last_passed_exam_result(db, user_id, exclude_attempt_id=exclude_attempt_id)
    if passed is None:
        return ""
    return format_exam_result_line(grade=passed.grade, percent=passed.percent)


def _profile_form_values(db: Session, user: User) -> ProtocolFormValues:
    now = dt.datetime.now(dt.timezone.utc)
    full_name = (user.full_name or user.username or "").strip()
    job = (user.job_title or "").strip()
    return ProtocolFormValues(
        protocol_number=f"{now:%Y}{user.id:05d}",
        check_date=now.strftime("%d.%m.%Y"),
        check_reason="очередная",
        regulatory_docs="Правила по охране труда при эксплуатации электроустановок",
        examinee_name=full_name,
        workplace=_workplace_from_business_unit(user),
        position=job,
        previous_check_date=_previous_check_date(db, user.id),
        exam_grade=_exam_grade_text(db, user.id),
        safety_group=_safety_group_for_user(user),
        result_installations=_installations_exam_result(db, user.id),
    )


def _signed_form_values(db: Session, protocol: SignedProtocol) -> ProtocolFormValues:
    signed = protocol.signed_at.astimezone(dt.timezone.utc)
    pct = float(protocol.result_percent)
    grade = grade_for_exam_protocol(pct)
    return ProtocolFormValues(
        protocol_number=f"{signed:%Y}{protocol.attempt_id:05d}",
        check_date=signed.strftime("%d.%m.%Y"),
        check_reason="по результатам проверки на платформе «Развивайся»",
        regulatory_docs=protocol.test_title,
        examinee_name=protocol.examinee_full_name.strip(),
        workplace=_signed_workplace(protocol),
        position=protocol.examinee_job_title.strip(),
        previous_check_date=_previous_check_date(
            db, protocol.examinee_id, exclude_attempt_id=protocol.attempt_id
        ),
        exam_grade=grade,
        safety_group=(
            _safety_group_for_user(protocol.examinee) if protocol.examinee is not None else ""
        ),
        result_installations=_installations_exam_result(
            db, protocol.examinee_id, percent=pct, grade=grade
        ),
    )


def _attempt_protocol_form_values(
    db: Session, attempt: Attempt, examinee: User, test: Test
) -> ProtocolFormValues:
    finished = attempt.finished_at
    if finished is None:
        raise ValueError("attempt is not finished")
    finished_utc = finished.astimezone(dt.timezone.utc)
    summary = score_attempt(db, attempt)
    grade = grade_for_exam_protocol(summary.percent)
    return ProtocolFormValues(
        protocol_number=f"{finished_utc:%Y}{attempt.id:05d}",
        check_date=finished_utc.strftime("%d.%m.%Y"),
        check_reason="по результатам проверки на платформе «Развивайся»",
        regulatory_docs=(test.title or "").strip()
        or "Правила по охране труда при эксплуатации электроустановок",
        examinee_name=str(examinee.full_name or examinee.username or "").strip(),
        workplace=_workplace_from_business_unit(examinee),
        position=str(examinee.job_title or "").strip(),
        previous_check_date=_previous_check_date(
            db, examinee.id, exclude_attempt_id=attempt.id
        ),
        exam_grade=grade,
        safety_group=_safety_group_for_user(examinee),
        result_installations=_installations_exam_result(
            db,
            examinee.id,
            exclude_attempt_id=attempt.id,
            percent=summary.percent,
            grade=grade,
        ),
    )


def build_protocol_pdf(db: Session, user: User) -> bytes:
    return _render_protocol_pdf(_profile_form_values(db, user))


def build_examinee_protocol_form_pdf(
    db: Session, attempt: Attempt, examinee: User, test: Test
) -> bytes:
    return _render_protocol_pdf(_attempt_protocol_form_values(db, attempt, examinee, test))


def build_signed_protocol_pdf(db: Session, protocol: SignedProtocol) -> bytes:
    return _render_protocol_pdf(_signed_form_values(db, protocol))
