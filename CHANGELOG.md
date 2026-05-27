# Changelog

Формат основан на [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/),
версии по [Semantic Versioning](https://semver.org/lang/ru/).

## [Unreleased]

## [0.5.0] - 2026-05-27

### Added

- **Сервисный слой** (`app/services/`): бизнес-логика вынесена из контроллеров (`AuthService`, `TestService`, `DashboardService`, `ProfileService`, `ManualService`).
- **FormRequest** (`app/form_requests/`): валидация входных данных через Pydantic-модели (`RegisterRequest`, `LoginRequest`, `TestCreateRequest`, `TicketSaveRequest`, `SubmitExamRequest`, `ProfileUpdateRequest`).
- **Репозитории** (`app/repositories/`) с **eager loading** (`selectinload`) для тестов, попыток и дашборда — устранение N+1.
- **TTL-кэш** (`app/cache.py`, `cachetools`) для списка мануалов; настройка `CACHE_TTL_SECONDS`.
- **Хэширование паролей**: bcrypt через passlib, настраиваемая сложность `BCRYPT_ROUNDS`.
- **CI/CD**: job `deploy` на ветке `main` — сборка production-образа, smoke-deploy и опциональная публикация в GHCR (`GHCR_TOKEN`).
- `docker-compose.prod.yml` и скрипт `scripts/deploy.sh` для деплоя.

### Changed

- Контроллеры `app/api/*` стали тонкими: делегируют сервисам и маппят `AppError` → HTTP.
- Экзамен по билетам документирован в README (сессия, билеты по одному, finish).
- README актуализирован: архитектура, роли, Docker, CI/CD.

## [0.4.0] - 2026-05-26

### Added

- Защита **CSRF**: `CSRFMiddleware`, `GET /api/auth/csrf`, заголовок `X-CSRF-Token` в axios.
- Корреляционные ID для трассировки: заголовок `X-Correlation-ID` + middleware.
- Rate limiting через Redis (опционально) для защиты API.
- Централизованная обработка ошибок API на клиенте: 401/403/500 в interceptor axios.
- API-тесты: `pytest` + `pytest-asyncio` + `httpx` для FastAPI.
- Dockerfile + `docker-compose` + CI workflow.
- Валидация конфигурации через `pydantic-settings`.
- Роли пользователей: **admin**, **Еж** (`ezh`), **Кот** (`kot`); создание/редактирование тестов — только admin и Еж.
- Раздел **Мануалы** (`/manuals`, `GET /api/manuals`).
- Профиль Кота (ФИО, дата рождения, должность) и формирование **PDF-протокола** (`GET /api/profile/protocol.pdf`).
- Запрет выделения текста в билетах (CSS `user-select: none`).
- Синхронизация UI-макета **razvivaisia** с React: CSS, layout, кабинет, мануалы, статические прототипы в `frontend/public/razvivaisia/`.
- **JSON REST API** под префиксом `/api` (auth, dashboard, tests, exam).
- **Frontend:** React + TypeScript + Vite (`frontend/`), UI дашборда «Развивайся».
- CORS для `localhost:5173`, раздача SPA из `frontend/dist` в production.

### Removed

- HTML-маршруты `app/routes.py` (Jinja); UI перенесён в React.

## [0.3.0] - 2026-05-26

### Added

- `app/constants.py` — единый источник лимитов и порогов.
- `app/attempt_service.py` — сохранение попыток и подсчёт результатов без дублирования в маршрутах.
- `README.md` с описанием установки и структуры.
- На странице результата: статус «экзамен сдан / не сдан» (порог 70%).

### Changed

- Рефакторинг `routes.py`: общие хелперы каталога, проверка автора, единый `_dashboard_context`.
- `dashboard_stats.py` использует `attempt_service` для последней попытки.
- `validation.py` импортирует константы из `constants.py`.
- Удалены неиспользуемые `base.html` и `style.css` (интерфейс на `dashboard.css`).

## [0.2.0] - 2026-05-13

### Added

- Оценочная шкала по доле правильных ответов: &lt;75% — неудовлетворительно; 75–85% — удовлетворительно; 85–95% — хорошо; от 95% — отлично (`app/grading.py`).
- Отображение оценки и процента на странице результата теста и в личном кабинете; разбивка по билетам.
- Интерфейс личного кабинета «Развивайся»: боковое меню, карточки, «Обучение», «Экзамен».

### Changed

- В одном билете **10 вопросов** (ранее три): создание, сохранение, валидация, шаблоны.

## [0.1.0] - 2026-05-13

### Added

- FastAPI: регистрация, сессии, личный кабинет, каталог, прохождение тестов.
- PostgreSQL (SQLAlchemy + `psycopg` v3).
- До **500** билетов на тест; варианты **A–D / 1–4**.
- Редактирование только автором; защита редиректов для чужих пользователей.
