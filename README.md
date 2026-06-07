# Развивайся — экзамен по электробезопасности

**Backend:** FastAPI + PostgreSQL (JSON API)  
**Frontend:** React 18 + TypeScript + Vite

Архитектура: [ARCHITECTURE.md](ARCHITECTURE.md) · Деплой: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) · **Ubuntu 26.04:** [docs/DEPLOYMENT_UBUNTU_2604.md](docs/DEPLOYMENT_UBUNTU_2604.md) · Бизнес-правила: [docs/BUSINESS_RULES.md](docs/BUSINESS_RULES.md) · API: `/docs` (OpenAPI)

## Быстрый старт (разработка)

### 1. База и backend

```bash
cd exam_tests
python3 -m pip install -r requirements.txt
cp .env.example .env
# отредактируйте DATABASE_URL и SECRET_KEY
createdb exam_tests

uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

API: http://127.0.0.1:8000/api/health  
Документация: http://127.0.0.1:8000/docs

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

UI: http://127.0.0.1:5173 — запросы `/api/*` проксируются на backend.

Сессия: cookie `exam_session`, axios с `withCredentials: true`.

### CSRF

1. При старте UI: `GET /api/auth/csrf` → токен в сессии и в памяти клиента.
2. Все **POST/PUT/DELETE** отправляют заголовок **`X-CSRF-Token`** (см. `frontend/src/api/csrf.ts`).
3. Backend (`CSRFMiddleware`) сверяет заголовок с `session["csrf_token"]`.

## Docker

Корень репозитория должен содержать `compose.yaml`. Если Docker Desktop показывает **«no configuration file provided: not found»**, запускайте команды из этого каталога или см. [docs/DOCKER.md](docs/DOCKER.md).

```bash
cd exam_tests   # каталог с compose.yaml
docker compose up -d db redis
docker compose build backend
docker compose run --rm backend pytest   # тесты
docker compose up backend                # API на :8000
```

- **UI в том же контейнере:** после `docker compose build backend` откройте http://127.0.0.1:8000/ (не только `/docs`).
- **UI с hot-reload:** `docker compose up -d frontend` → http://127.0.0.1:5173 (см. [docs/DOCKER.md](docs/DOCKER.md)).

`Dockerfile` собирает frontend из корректного `WORKDIR /app/frontend`.

Production-стек:

```bash
export SECRET_KEY=$(openssl rand -hex 32)
./scripts/deploy.sh
# или: docker compose -f docker-compose.prod.yml up -d
```

## CI/CD

GitHub Actions (`.github/workflows/ci.yml`):

| Job | Когда | Действие |
|-----|-------|----------|
| **lint** | push / PR | `ruff check` |
| **test** | push / PR | `docker compose up db redis`, pytest + coverage |
| **frontend** | push / PR | `npm run build` |
| **deploy** | push в `main` | сборка prod-образа, smoke-deploy, healthcheck |

Опционально: секрет `GHCR_TOKEN` — публикация образа в GitHub Container Registry.

Критические фиксы деплоя:
- в `deploy` job задан `SECRET_KEY` уже на этапе сборки;
- `scripts/deploy.sh` — build, up и healthcheck; при ошибке стек остаётся для диагностики (тома не трогаются).

## Миграции (Alembic)

- Локально: `AUTO_CREATE_SCHEMA=true` (схема через `create_all` при старте) **или** `alembic upgrade head`.
- Production (`docker-compose.prod.yml`): `AUTO_CREATE_SCHEMA=false`, `RUN_MIGRATIONS=true` — entrypoint выполняет `alembic upgrade head` перед uvicorn.

```bash
# применить миграции вручную
export DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/exam_tests
./scripts/migrate.sh
# или: alembic upgrade head
alembic revision --autogenerate -m "описание"   # новая ревизия
```

Начальная ревизия: `alembic/versions/001_initial_schema.py`.

## PDF и шрифты

Кириллица в PDF: DejaVu в `app/static/fonts/` (установка: `./scripts/fetch-dejavu-fonts.sh`). В Docker также ставится пакет `fonts-dejavu-core`.

## Экспорт (async)

Задачи экспорта профиля (PDF/CSV) хранятся в **Redis** при заданном `REDIS_URL`; без Redis — in-memory fallback (только dev/тесты). TTL: `EXPORT_TASK_TTL_SECONDS` (по умолчанию 3600).

## Безопасность

- **Пароли:** bcrypt через passlib (`app/auth_utils.py`), сложность — `BCRYPT_ROUNDS` (по умолчанию 12).
- **Сессии:** HttpOnly-cookie, настройки `SESSION_COOKIE_*`.
- **CSRF** на мутирующих запросах.
- **Защита от брутфорса логина:** in-memory limiter, параметры `LOGIN_RATE_LIMIT_ATTEMPTS` и `LOGIN_RATE_LIMIT_WINDOW_SECONDS`.
- **Аудит критических действий:** логины, регистрации, запреты редактирования (`SecurityAuditService`).
- **Экспорт-задачи привязаны к пользователю:** скачивание по `task_id` проверяет владельца; состояние задачи в Redis (см. выше).

## Роли

| Роль | Код | Возможности |
|------|-----|-------------|
| Администратор | `admin` | всё |
| Еж | `ezh` | создание и редактирование тестов |
| Кот | `kot` | обучение, экзамен, мануалы, профиль, PDF-протокол |

Подробные бизнес-правила (порог сдачи **75%**, состав экзамена, доступ к протоколам): [docs/BUSINESS_RULES.md](docs/BUSINESS_RULES.md).

## Основные API (JSON)

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/auth/csrf` | CSRF-токен |
| GET | `/api/auth/me` | Текущий пользователь или `null` |
| POST | `/api/auth/register` | Регистрация (FormRequest) |
| POST | `/api/auth/login` | Вход |
| POST | `/api/auth/logout` | Выход |
| GET | `/api/dashboard` | Личный кабинет |
| GET | `/api/tests` | Список тестов |
| POST | `/api/tests` | Создать тест (admin/ezh) |
| GET | `/api/tests/{id}` | Редактирование (admin/ezh) |
| GET | `/api/tests/{id}/training` | Билеты для тренировки |
| POST | `/api/tests/{id}/training` | Отправить ответы (тренировка) |
| POST | `/api/tests/{id}/exam/session` | Начать экзамен |
| GET | `/api/tests/{id}/exam/session` | Статус сессии |
| GET | `/api/tests/{id}/exam/tickets/{ticket_id}` | Билет (20 мин) |
| POST | `/api/tests/{id}/exam/tickets/{ticket_id}` | Ответы по билету |
| POST | `/api/tests/{id}/exam/finish` | Завершить экзамен |
| GET | `/api/tests/{id}/exam/attempts/{attempt_id}/result` | Результат экзамена (экзаменуемый) |
| POST | `/api/tests/{id}/exam/attempts/{attempt_id}/protocol/sign` | Подписать протокол (admin/ezh) |
| GET | `/api/tests/{id}/exam/attempts/{attempt_id}/protocol` | Метаданные подписанного протокола |
| GET | `/api/tests/{id}/exam/attempts/{attempt_id}/protocol.pdf` | PDF подписанного протокола |
| POST/PUT/DELETE | `/api/tests/{id}/tickets/...` | CRUD билетов |
| GET/PUT | `/api/profile` | Профиль Кота |
| GET | `/api/profile/protocol.pdf` | PDF-протокол |
| POST | `/api/profile/protocol.pdf/export` | Асинхронный экспорт PDF-протокола |
| POST | `/api/profile/attempts/export` | Асинхронный экспорт результатов (CSV) |
| GET | `/api/profile/exports/{task_id}` | Статус/скачивание результата фоновой задачи |
| GET | `/api/manuals` | Список мануалов (кэш TTL) |
| GET | `/api/admin/users` | Список пользователей (**только admin**) |
| PUT | `/api/admin/users/{user_id}/role` | Смена роли (**только admin**) |

### Смена роли через API

1. Войти под пользователем с ролью `admin` (`POST /api/auth/login` + cookie сессии).
2. Получить CSRF: `GET /api/auth/csrf` → заголовок `X-CSRF-Token` на мутирующих запросах.
3. Список пользователей: `GET /api/admin/users`.
4. Смена роли: `PUT /api/admin/users/{user_id}/role` с телом `{"role": "ezh"}` (допустимо: `admin`, `ezh`, `kot`).

Ограничения: нельзя изменить **свою** роль; без роли `admin` — ответ `403`.

Пример (curl, после логина cookie сохранён в `cookies.txt`):

```bash
CSRF=$(curl -s -b cookies.txt -c cookies.txt http://127.0.0.1:8000/api/auth/csrf | jq -r .csrf_token)
curl -s -b cookies.txt -c cookies.txt \
  -X PUT "http://127.0.0.1:8000/api/admin/users/2/role" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: $CSRF" \
  -d '{"role":"admin"}'
```

Первого администратора при пустой БД можно задать SQL: `UPDATE users SET role = 'admin' WHERE username = '...';`

## Архитектура backend

```
app/
├── api/              # Тонкие контроллеры (FastAPI routes)
├── form_requests/    # Валидация входа (аналог Laravel FormRequest)
├── services/         # Бизнес-логика (в т.ч. подпапки modules/*)
├── dto/              # Data Transfer Objects
├── policies/         # Правила доступа (Policies)
├── repositories/     # Запросы к БД + eager loading (selectinload)
├── cache.py          # TTL-кэш (cachetools)
├── auth_utils.py     # bcrypt hash/verify
├── exceptions.py     # AppError → HTTP
└── main.py
```

**Оптимизация БД:** репозитории загружают связи (`Test.tickets.questions`, `Attempt.test`) через eager loading; список мануалов кэшируется in-memory (`CACHE_TTL_SECONDS`).  
**Проверка N+1:** добавлен тест с подсчётом SQL-запросов в `tests/test_services.py`.

## Ограничения async-экспортов

Текущая реализация задач экспорта хранится in-memory в процессе API. Это подходит для dev/single-worker, но в production лучше вынести состояние в Redis/БД и использовать отдельную очередь задач.

## Тесты

```bash
pip install -r requirements-dev.txt
pytest
# или через Docker:
docker compose run --rm backend pytest
```

Покрытие, добавленное в рамках рефакторинга:
- unit-тесты сервисов;
- unit-тесты политик доступа;
- интеграционные тесты API (async exports, login brute-force limiter).

## Production (без Docker)

```bash
cd frontend && npm run build
cd .. && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

После `npm run build` FastAPI отдаёт SPA из `frontend/dist/`.

## Структура проекта

```
exam_tests/
├── app/
├── frontend/
├── tests/
├── scripts/
├── compose.yaml
├── docker-compose.prod.yml
└── .github/workflows/ci.yml
```

Старые Jinja-шаблоны (`app/templates/`) больше не используются — UI только в React.
