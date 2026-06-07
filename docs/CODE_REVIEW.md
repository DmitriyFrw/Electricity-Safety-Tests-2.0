# Чек-лист code review

## Типы

- [ ] `mypy` проходит локально: `pip install -r requirements-dev.txt && mypy`
- [ ] Новые публичные функции с аннотациями аргументов и возврата

## Архитектура

- [ ] Бизнес-логика в `app/services/`, не в роутерах
- [ ] SQL через `repositories/`, без N+1 (`selectinload` в `options.py`)
- [ ] `AppError` вместо `HTTPException` в сервисах
- [ ] Новые ответы API — через `api/mappers.py` + `schemas.py`
- [ ] Сервисы без `fastapi.Request` — `HttpContext` / порты (`docs/ARCHITECTURE_QUALITY.md`)
- [ ] Внутренние DTO — Pydantic `ValidatedDTO`, не «голый» dataclass
- [ ] Новый use case: `*Command`/`*Query` + handler + `registry.py` (см. `docs/CQRS.md`)

## Безопасность

- [ ] Мутирующие запросы с CSRF (`X-CSRF-Token`)
- [ ] Export task: проверка `owner_user_id`
- [ ] Подписанный протокол: `examinee_id` / `signer_id` / staff (`…/protocol`, `…/protocol.pdf`)
- [ ] Пароли только через `support/passwords`
- [ ] Секреты не в репозитории

## Тесты

- [ ] Pytest для новых сценариев и edge cases
- [ ] Политики и N+1 (`tests/test_policies.py`, `tests/test_services.py`)
- [ ] Coverage не падает (CI `--cov-fail-under`)

## API

- [ ] OpenAPI-теги и `response_model`
- [ ] Коды ошибок согласованы (`AppError.status_code`)

## Frontend (если затронут)

- [ ] `axiosErrorMessage` для ошибок API
- [ ] Типы в `frontend/src/types/api.ts`

## Деплой

- [ ] Миграция Alembic при изменении моделей
- [ ] CHANGELOG / README при пользовательских изменениях
