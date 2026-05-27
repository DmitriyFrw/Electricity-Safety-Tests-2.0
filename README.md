# Развивайся — экзамен по электробезопасности

**Backend:** FastAPI + PostgreSQL (JSON API)  
**Frontend:** React 18 + TypeScript + Vite

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

### Цепочка данных (getReact → state)

1. React вызывает **`getReact<T>('/dashboard')`** (`frontend/src/api/getReact.ts`) — внутри **axios.get**.
2. Backend (`/api/...`) отвечает **JSON**.
3. Хук **`useGetReact`** кладёт ответ в **`useState`**: `{ data, loading, error }`.

```tsx
const { data, loading, error } = useGetReact<Dashboard>("/dashboard");
// data обновляется после GET — UI перерисовывается
```

## Production

```bash
cd frontend && npm run build
cd .. && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

После `npm run build` FastAPI отдаёт SPA из `frontend/dist/`.

## Основные API (JSON)

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/auth/me` | Текущий пользователь или `null` |
| POST | `/api/auth/register` | Регистрация |
| POST | `/api/auth/login` | Вход |
| POST | `/api/auth/logout` | Выход |
| GET | `/api/dashboard` | Данные личного кабинета |
| GET | `/api/tests` | Список тестов |
| POST | `/api/tests` | Создать тест |
| GET | `/api/tests/{id}` | Редактирование (автор) |
| GET | `/api/tests/{id}/exam` | Билеты для сдачи |
| POST | `/api/tests/{id}/exam` | Отправить ответы |
| POST | `/api/tests/{id}/tickets` | Добавить билет |
| PUT | `/api/tests/{id}/tickets/{ticket_id}` | Сохранить билет |
| DELETE | `/api/tests/{id}/tickets/{ticket_id}` | Удалить билет |

## Структура

```
exam_tests/
├── app/
│   ├── api/           # JSON-маршруты
│   ├── main.py
│   ├── schemas.py
│   └── ...
└── frontend/
    └── src/
        ├── api/client.ts
        └── pages/
```

Старые Jinja-шаблоны (`app/templates/`) больше не используются — UI только в React.
