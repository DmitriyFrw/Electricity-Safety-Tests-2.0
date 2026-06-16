# CQRS (Command / Query)

## Шина

- **`CommandBus`** — изменение состояния (`app/cqrs/bus.py`)
- **`QueryBus`** — чтение (`dispatch` по типу сообщения)
- Регистрация: `app/cqrs/registry.py`
- Доступ из API: `get_command_bus()`, `get_query_bus()` (`app/cqrs/deps.py`)

```python
from app.cqrs import get_command_bus, get_query_bus
from app.cqrs.messages.tests import ListTestsQuery

result = get_query_bus().dispatch(ListTestsQuery(db=db, user=user))
```

## Сообщения

| Тип | Пакет | Пример |
|-----|--------|--------|
| Query | `app/cqrs/messages/*.py` | `ListTestsQuery`, `GetDashboardQuery` |
| Command | то же | `CreateTestCommand`, `LoginUserCommand` |

Сообщения — `frozen` dataclass с полями контекста (`db`, `user`, `form`, …).

## Обработчики

Класс с методом `handle(message) -> Result`:

```
app/cqrs/handlers/
  auth.py
  tests_catalog.py
  tests_editor.py
  tests_training.py
  tests_exam.py
  tests_protocols.py
  profile.py
  dashboard.py
  manuals.py
  exports.py
```

Новая операция:

1. Добавить `*Query` или `*Command` в `messages/`
2. Реализовать `*Handler` в `handlers/`
3. Зарегистрировать в `registry.py`
4. Вызвать из `app/api/*` через `dispatch`

## Точка входа HTTP

Роутеры вызывают только `dispatch_command` / `dispatch_query`. Общие проверки доступа к тесту — `app/support/test_access.py`.
