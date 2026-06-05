# Docker и Docker Desktop

## Ошибка «no configuration file provided: not found»

Сообщение выдаёт **CLI Docker Compose**, когда команда (`logs`, `up`, `ps`, …) запускается **не из каталога**, где лежит compose-файл.

В корне репозитория должен быть **`compose.yaml`** (dev-стек). Production — **`docker-compose.prod.yml`**.

### Что сделать

1. Откройте терминал в корне проекта (там, где `compose.yaml`):

   ```bash
   cd /path/to/exam_tests
   docker compose ps
   ```

   Если `ps` работает без ошибки — путь верный.

2. **Docker Desktop → Logs** привязан к compose-проекту только если стек поднят из этого каталога:

   ```bash
   docker compose up -d db redis
   docker compose up -d backend
   ```

3. Контейнеры от **`docker compose run --rm backend …`** (pytest, mypy) — разовые. В Logs Desktop для них compose-файл часто не находится. Смотрите логи так:

   ```bash
   docker logs <container_id>
   ```

   или из корня проекта:

   ```bash
   docker compose logs -f backend
   ```

4. В Docker Desktop: **Containers** → проект **exam_tests** → сервис **backend** → вкладка **Logs** (не общий Logs без выбранного compose-проекта).

## Обычный запуск

```bash
cd exam_tests
docker compose up -d db redis
docker compose build backend
docker compose up -d backend
docker compose logs -f backend
```

API: http://localhost:8000/api/health

## Frontend из Docker Desktop

Есть **два режима**.

### 1. Собранный UI внутри backend (как в production)

При сборке `backend` в образ попадает `frontend/dist`. Отдельный контейнер для UI не нужен.

```bash
cd exam_tests
docker compose build backend
docker compose up -d db redis backend
```

Откройте в браузере:

- **UI (React):** http://127.0.0.1:8000/
- **API / Swagger:** http://127.0.0.1:8000/docs

Если на `:8000/` только 404 — пересоберите образ (`docker compose build --no-cache backend`).

### 2. Dev-сервер Vite в отдельном контейнере (hot-reload)

В `compose.yaml` есть сервис **`frontend`** (порт **5173**).

```bash
cd exam_tests
docker compose up -d db redis backend
docker compose up -d frontend
```

В Docker Desktop: **Containers** → **exam_tests-frontend-1** → **Logs** (должен быть `Local: http://localhost:5173/`).

Браузер: **http://127.0.0.1:5173** — запросы `/api` проксируются на backend на хосте `:8000`.

Остановить только UI:

```bash
docker compose stop frontend
```

### Без Docker (классическая разработка)

```bash
# терминал 1 — backend уже в Docker на :8000
# терминал 2
cd frontend && npm install && npm run dev
```

http://127.0.0.1:5173

## Production

```bash
docker compose -f docker-compose.prod.yml up -d
```
