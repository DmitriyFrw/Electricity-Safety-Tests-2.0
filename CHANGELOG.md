# Changelog

Формат основан на [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/),
версии по [Semantic Versioning](https://semver.org/lang/ru/).

## [Unreleased]

### Added

- **CQRS**: `CommandBus` / `QueryBus`, сообщения (`app/cqrs/messages/`), обработчики (`app/cqrs/handlers/`), регистрация в `registry.py`; API вызывает `dispatch`. Документация: `docs/CQRS.md`.
- Порты и адаптеры HTTP: `SessionStore`, `HttpContext` (отвязка `AuthService` от `fastapi.Request`).
- Валидация внутренних DTO через Pydantic (`ValidatedDTO`).
- **mypy strict** в CI (`pyproject.toml`, stub-пакеты `types-*`).
- Рефакторинг слоёв: `app/services/{tests,users,exams,attempts,pdf}/`, `app/support/`, `app/api/{deps,mappers,handlers}`, репозитории по сущностям.
- Разделение `TestService` на Catalog / Editor / Training / Exam / Protocols (фасад сохранён).
- Кэш списка тестов (`TEST_LIST_CACHE_TTL_SECONDS`), глобальный handler `AppError`.
- Документация: `ARCHITECTURE.md`, `docs/DEPLOYMENT.md`, `docs/BUSINESS_RULES.md`, `docs/CODE_REVIEW.md`.
- CI: ruff, **mypy strict** (`pyproject.toml`), pytest-cov, сборка frontend.
- DejaVu TTF в `app/static/fonts/` и `scripts/fetch-dejavu-fonts.sh`; Docker: `fonts-dejavu-core` + копирование шрифтов при сборке.
- Alembic: `alembic/`, начальная ревизия `001_initial_schema`, `scripts/migrate.sh`, entrypoint с `alembic upgrade head` в production.
- Асинхронный экспорт тяжёлых операций:
  - `POST /api/profile/protocol.pdf/export` (PDF),
  - `POST /api/profile/attempts/export` (CSV),
  - `GET /api/profile/exports/{task_id}` (статус/скачивание).
- DTO-слой: `app/dto/*` (`AuditEventDTO`, `ExportRequestDTO`, `ExportTaskDTO`).
- Policies-слой: `app/policies/access_policy.py` и интеграция в зависимости/роли.
- Безопасность логина: лимит неудачных попыток входа (защита от брутфорса) через `LOGIN_RATE_LIMIT_ATTEMPTS` и `LOGIN_RATE_LIMIT_WINDOW_SECONDS`.
- Аудит-логирование критических событий (логины/регистрация/запреты изменения).
- Новые тесты:
  - `tests/test_policies.py` (политики),
  - `tests/test_services.py` (сервисы + проверка N+1 по числу SQL-запросов),
  - интеграционные API тесты async exports и login rate limiting.

### Changed

- Порог сдачи экзамена: **75%** (удовлетворительно и выше); документация приведена в соответствие с `MIN_PASS_PERCENT`.
- Экзамен: один случайный билет из пула тестов группы ЭБ; состав вопросов фиксируется в попытке.
- CI job `lint`: проверка типов `mypy` (режим `strict`) после `ruff`; конфиг в `pyproject.toml`, scope — `app/` (legacy `routes.py`, `services/tests/` исключены).
- Типизация middleware, CQRS bus, DTO (`ExportTaskDTO.task_id` ≥ 8 символов).
- Время на экзаменационный билет увеличено с 10 до 20 минут (`EXAM_TICKET_TIME_LIMIT_SECONDS`).
- Сервисный слой разложен по подпапкам модулей в `app/services/*`.
- `LoginRateLimiter` исправлен: TTL кэша больше не мутируется на лету, кэш пересоздаётся при изменении TTL-конфига.
- Export-задачи привязаны к владельцу (`owner_user_id`), доступ к `GET /api/profile/exports/{task_id}` ограничен владельцем.
- Export-задачи хранятся в Redis (`ExportTaskStore`) при `REDIS_URL`; in-memory fallback без Redis.
- `AUTO_CREATE_SCHEMA` вынесен в конфиг: в production можно отключить `create_all()` и использовать миграции.
- PDF-сервис получил поддержку кириллических TTF-шрифтов (DejaVu/Noto-совместимый fallback), при отсутствии — безопасный fallback на Helvetica.
- Исправлена frontend-сборка в `Dockerfile`: сборка выполняется из `WORKDIR /app/frontend`.
- Исправлены критические проблемы deploy:
  - `SECRET_KEY` прокинут в CI на этапе build production image,
  - `scripts/deploy.sh` очищает стек при failed healthcheck.

### Fixed

- **IDOR** на `GET …/protocol` и `GET …/protocol.pdf`: доступ только экзаменуемому, подписанту или staff (`admin`/`ezh`).

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
