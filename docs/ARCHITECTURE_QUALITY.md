# Качество архитектуры (Laravel review → FastAPI)

Чек-лист из code review Laravel-проекта и **как это закрыто** в «Развивайся» (Python/FastAPI).

## 1. Dependency Injection

| Laravel | FastAPI / проект |
|---------|------------------|
| Service Container, жирные конструкторы | `Depends()` в `app/api/deps.py`; сервисы — **статические use-case** без конструкторов |
| Много зависимостей в контроллере | Группировка: `AuthenticatedDb` (`app/api/context.py`) — `db` + `user` одним объектом |
| Ленивая загрузка | `app/services/__init__.py` → `__getattr__` (ленивые импорты фасадов) |

**Правило:** новые эндпоинты с `db` + `login_required` могут принимать `Annotated[AuthenticatedDb, Depends(get_authenticated_db)]` вместо двух отдельных `Depends`.

**Не делать:** внедрять `Session`, `Request`, `HTTPException` в сервисы.

## 2. CQRS

Реализовано: **`CommandBus`**, **`QueryBus`**, типизированные сообщения и классы-обработчики (`app/cqrs/`).

Подробно: **[CQRS.md](CQRS.md)**.

**Правило:** новый use case = `*Command` / `*Query` + `*Handler` + регистрация в `registry.py`; API вызывает только `dispatch`.

## 3. Связь с фреймворком

| Проблема | Решение в проекте |
|----------|-------------------|
| Сервисы зависят от `Request` | Порт `SessionStore` (`app/ports/`), адаптер `HttpContext` (`app/adapters/`). `AuthService` принимает `HttpContext`, не `Request` |
| CSRF / cookies | Только в API: `rotate_csrf_token(request)` после login/register |
| Сборка JSON | `app/api/mappers.py` — допустимо в API; в сервисах — только при отсутствии дублирования (постепенно выносить в mappers) |

**Следующий шаг (по мере роста):** `Protocol` для `ExportTaskStore`, `LoginRateLimiter` backend.

## 4. Валидация DTO

| Слой | Валидация |
|------|-----------|
| HTTP body | `app/form_requests/*` (Pydantic, аналог Form Request) |
| Ответ API | `app/schemas.py` |
| Внутренние границы | `app/dto/*` наследуют `ValidatedDTO` (Pydantic, `extra=forbid`) |

Примеры: `ExportRequestDTO`, `AuditEventDTO`. Создание: `ExportRequestDTO.model_validate({...})` или конструктор с автоматической проверкой полей.

## 5. Типизация

В PHP: `declare(strict_types=1)`. В Python эквивалент:

- `from __future__ import annotations` во всех новых модулях `app/`
- Аннотации аргументов и возвратов в публичных методах сервисов и репозиториев
- CI: Ruff + (опционально) `mypy` strict для `app/`

**Не путать:** `@dataclass` без Pydantic для DTO на границах сервисов — заменять на `ValidatedDTO`.

## Статус внедрения

| Пункт | Статус |
|-------|--------|
| DI / группировка | ✅ `deps`, `AuthenticatedDb`, ленивые сервисы |
| CQRS | ✅ `app/cqrs/` — CommandBus, QueryBus, handlers |
| Отвязка от FastAPI в сервисах | ✅ Auth; 🟡 mappers в части exam-сервисов |
| DTO + валидация | ✅ Pydantic DTO |
| Strict typing | ✅ mypy `strict` в CI (`pyproject.toml`) |
