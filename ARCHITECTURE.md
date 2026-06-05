# Архитектура «Развивайся»

Стек: **FastAPI** + **SQLAlchemy 2** + **PostgreSQL** + **Redis** + **React/Vite**.

> Проект на Python/FastAPI. Рекомендации в стиле Laravel (Eloquent, FormRequest, Queues) здесь отражены эквивалентами: ORM, Pydantic, фоновые export-задачи.

## Слои

```
┌─────────────────────────────────────────────────────────┐
│  frontend/          React SPA, axios + cookie session   │
└───────────────────────────┬─────────────────────────────┘
                            │ /api/*
┌───────────────────────────▼─────────────────────────────┐
│  app/api/           Роутеры (тонкие контроллеры)       │
│    deps.py          DI: login_required, роли            │
│    mappers.py       ORM → Pydantic (ответы API)         │
│    handlers.py      AppError → JSON 4xx                │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│  app/cqrs/          CommandBus / QueryBus + handlers    │
│  app/services/      Фасады над шиной (TestService, …)  │
│    users/           AuthService → CommandBus            │
│    attempts/        Подсчёт баллов, тренировка          │
│    exams/           Сессия экзамена, таймер билета      │
│    pdf/             Генерация PDF                       │
│    exports/         Async export (Redis / memory)       │
│    security/        Audit, login rate limit             │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│  app/repositories/  Доступ к БД, eager loading (N+1)    │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│  app/models.py      SQLAlchemy ORM                      │
└─────────────────────────────────────────────────────────┘

  app/support/        Чистые хелперы (grading, validation, passwords)
  app/ports/          Интерфейсы (SessionStore) — без FastAPI
  app/adapters/       Адаптеры HTTP (HttpContext)
  app/dto/            Внутренние DTO с Pydantic-валидацией
  app/schemas.py      Pydantic — контракт OpenAPI / ответы API
  app/form_requests/  Pydantic — тела запросов (валидация входа)
  app/policies/       Правила доступа по ролям
  app/api/context.py  AuthenticatedDb — группировка Depends
```

## Зависимости между модулями

- **API** не обращается к ORM напрямую (кроме `deps`).
- **Сервисы** используют **repositories** и **support**, не FastAPI.
- **DTO** (`app/dto/`) — только для внутренних границ (export, audit), не дублируют `schemas.py`.
- **Mappers** (`app/api/mappers.py`) — единое место сборки ответов JSON.

## Ключевые компоненты

| Компонент | Назначение |
|-----------|------------|
| `TestService` | Фасад над `CommandBus` / `QueryBus` (см. `docs/CQRS.md`) |
| `ExportService` + `ExportTaskStore` | Фоновый PDF/CSV (Redis или in-memory) |
| `LoginRateLimiter` | Защита логина (TTL cache) |
| `AccessPolicy` | admin / ezh / kot |
| Alembic | Миграции схемы (`AUTO_CREATE_SCHEMA=false` в prod) |

## OpenAPI / Swagger

- Интерактивная документация: `/docs`, `/redoc`
- Схемы генерируются из `app/schemas.py` и `form_requests/`

## Кэширование

- `TEST_LIST_CACHE_TTL_SECONDS` — список тестов (по умолчанию 1 ч)
- `CACHE_TTL_SECONDS` — прочие TTL-кэши (мануалы и т.д.)
- Инвалидация `test_list` при создании/редактировании билетов

## CQRS

См. **[docs/CQRS.md](docs/CQRS.md)** — сообщения, `CommandHandler` / `QueryHandler`, регистрация, примеры.

## Качество и паттерны (Laravel review)

См. **[docs/ARCHITECTURE_QUALITY.md](docs/ARCHITECTURE_QUALITY.md)** — DI, порты, DTO, типизация.

## Legacy

- `app/routes.py`, `app/web.py`, `app/templates/` — старый server-rendered UI, **не подключены** в `main.py`. Основной UI — React.

## CI/CD (см. `.github/workflows/ci.yml`)

1. Ruff (lint)
2. Pytest + coverage
3. Frontend `npm run build`
4. Docker deploy smoke

## Мониторинг (рекомендации)

- **Sentry**: `SENTRY_DSN` — подключить в `main.py` при необходимости
- Метрики: latency `/api/*`, pool DB, Redis export queue depth
- Health: `GET /api/health`
