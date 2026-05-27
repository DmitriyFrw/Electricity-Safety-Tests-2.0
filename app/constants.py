"""Общие константы приложения (единый источник правды)."""

MAX_TICKETS_PER_TEST = 500
QUESTIONS_PER_TICKET = 10

# Порог «сдан» на экзамене (подсказка в UI)
MIN_PASS_PERCENT = 70

# Отображение в карточке «Количество ошибок» (как в макете)
MAX_ERRORS_DISPLAY = 3

DEFAULT_SAFETY_GROUP = "IV"
DEFAULT_SAFETY_GROUP_DESC = "до и выше 1000 В"
KNOWLEDGE_CHECK_INTERVAL_DAYS = 365

# Лимит на один экзаменационный билет (секунды)
EXAM_TICKET_TIME_LIMIT_SECONDS = 10 * 60

ATTEMPT_MODE_TRAINING = "training"
ATTEMPT_MODE_EXAM = "exam"
