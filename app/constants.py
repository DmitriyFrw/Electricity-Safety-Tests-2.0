"""Общие константы приложения (единый источник правды)."""

MAX_TICKETS_PER_TEST = 500
QUESTIONS_PER_TICKET = 10
MIN_OPTION_COUNT = 2
MAX_OPTION_COUNT = 4

# Порог «сдан» на экзамене: удовлетворительно и выше (см. grade_for_percent, ≥ 75%)
MIN_PASS_PERCENT = 75

# Отображение в карточке «Количество ошибок» (как в макете)
MAX_ERRORS_DISPLAY = 3

SAFETY_GROUPS: tuple[str, ...] = ("I", "II", "III", "IV")
DEFAULT_KOT_SAFETY_GROUP = "II"
SAFETY_GROUP_DESCRIPTIONS: dict[str, str] = {
    "I": "",
    "II": "",
    "III": "",
    "IV": "",
}
# Обратная совместимость (старые импорты)
DEFAULT_SAFETY_GROUP = DEFAULT_KOT_SAFETY_GROUP
DEFAULT_SAFETY_GROUP_DESC = ""
KNOWLEDGE_CHECK_INTERVAL_DAYS = 365

# Лимит на один экзаменационный билет (секунды)
EXAM_TICKET_TIME_LIMIT_SECONDS = 20 * 60

ATTEMPT_MODE_TRAINING = "training"
ATTEMPT_MODE_EXAM = "exam"

# Роли пользователей
ROLE_ADMIN = "admin"
ROLE_EZH = "ezh"
ROLE_KOT = "kot"

ROLE_LABELS: dict[str, str] = {
    ROLE_ADMIN: "Администратор",
    ROLE_EZH: "Еж",
    ROLE_KOT: "Кот",
}

ROLES_CAN_EDIT_TESTS = frozenset({ROLE_ADMIN, ROLE_EZH})

# Юридические лица (бизнес-юниты) для профиля и строки «место работы» в протоколе PDF.
BUSINESS_UNITS: tuple[str, ...] = (
    "ДЦ MOZ",
    "ДЦ KLG",
    "ДЦ VLA",
    "ДЦ NRG",
    "ДЦ SAS",
)
ALLOWED_BUSINESS_UNITS = frozenset(BUSINESS_UNITS)

ASSIGNABLE_ROLES: tuple[str, ...] = (ROLE_ADMIN, ROLE_EZH, ROLE_KOT)
ALLOWED_ROLES = frozenset(ASSIGNABLE_ROLES)
