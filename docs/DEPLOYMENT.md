# Production: развёртывание базы данных и сайта

Пошаговое руководство по запуску платформы **Развивайся** (FastAPI + React) на сервере в production.  
Рекомендуемый способ — **Docker Compose** (`docker-compose.prod.yml`): PostgreSQL, Redis и backend (API + собранный UI) поднимаются одной командой.

**Подробный гайд для Ubuntu 26.04:** [DEPLOYMENT_UBUNTU_2604.md](DEPLOYMENT_UBUNTU_2604.md)

См. также: [DOCKER.md](DOCKER.md) (локальная разработка и типичные ошибки Docker Desktop).

---

## Содержание

1. [Архитектура production](#1-архитектура-production)
2. [Требования к серверу](#2-требования-к-серверу)
3. [Подготовка сервера](#3-подготовка-сервера)
4. [Клонирование репозитория](#4-клонирование-репозитория)
5. [Переменные окружения](#5-переменные-окружения)
6. [База данных PostgreSQL](#6-база-данных-postgresql)
7. [Redis](#7-redis)
8. [Первый деплой (пошагово)](#8-первый-деплой-пошагово)
9. [Миграции схемы (Alembic)](#9-миграции-схемы-alembic)
10. [Первый администратор](#10-первый-администратор)
11. [HTTPS и reverse proxy](#11-https-и-reverse-proxy)
12. [Проверка после деплоя](#12-проверка-после-деплоя)
13. [Резервное копирование и восстановление](#13-резервное-копирование-и-восстановление)
14. [Обновление версии](#14-обновление-версии)
15. [Откат](#15-откат)
16. [Мониторинг и логи](#16-мониторинг-и-логи)
17. [Типичные проблемы](#17-типичные-проблемы)
18. [Staging](#18-staging)
19. [Альтернатива: без Docker](#19-альтернатива-без-docker)

---

## 1. Архитектура production

```
                    ┌─────────────────────────────────────┐
  Браузер ──HTTPS──►│  Nginx / Caddy (80, 443)            │
                    │  TLS, прокси на localhost:8000      │
                    └──────────────────┬──────────────────┘
                                       │ HTTP
                    ┌──────────────────▼──────────────────┐
                    │  backend (один контейнер)           │
                    │  • FastAPI /api/*                   │
                    │  • React SPA из frontend/dist       │
                    │  • uvicorn :8000                    │
                    └───────┬──────────────────┬──────────┘
                            │                  │
              ┌─────────────▼──────┐   ┌───────▼────────┐
              │  PostgreSQL 16     │   │  Redis 7       │
              │  volume: db_data   │   │  rate limit,   │
              │  (только внутри    │   │  async export  │
              │   Docker-сети)     │   │                │
              └────────────────────┘   └────────────────┘
```

**Важно:**

- В production-образе frontend собирается на этапе `docker build`; отдельный контейнер для UI не нужен.
- Backend отдаёт статику и SPA-fallback из `frontend/dist/` (см. `app/main.py`).
- PostgreSQL и Redis **не пробрасываются наружу** в `docker-compose.prod.yml` — доступ только из Docker-сети.
- Схема БД создаётся **миграциями Alembic**, а не `create_all` (`AUTO_CREATE_SCHEMA=false`).

---

## 2. Требования к серверу

| Параметр | Минимум | Рекомендуется |
|----------|---------|---------------|
| ОС | Ubuntu 22.04/24.04/26.04 LTS, Debian 12 | то же |
| CPU | 2 vCPU | 2–4 vCPU |
| RAM | 2 GB | 4 GB |
| Диск | 20 GB SSD | 40+ GB SSD |
| Docker | Engine 24+ | последняя стабильная |
| Docker Compose | v2 (`docker compose`) | v2 |

**Сеть (входящие порты):**

| Порт | Назначение |
|------|------------|
| 22 | SSH (ограничить по IP при возможности) |
| 80, 443 | Reverse proxy (публичный доступ к сайту) |
| 8000 | Только localhost (прокси), **не открывать в интернет** |

**Программное обеспечение на сервере:**

- Git
- Docker Engine + плагин Compose
- (опционально) Nginx или Caddy для TLS
- (опционально) `certbot` для Let's Encrypt

---

## 3. Подготовка сервера

Пример для Ubuntu 24.04 под пользователем с `sudo`.

### 3.1. Обновление системы

```bash
sudo apt update && sudo apt upgrade -y
sudo timedatectl set-timezone Europe/Moscow   # или ваш часовой пояс
```

### 3.2. Установка Docker

Официальная инструкция: https://docs.docker.com/engine/install/ubuntu/

Кратко:

```bash
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker "$USER"
# перелогиньтесь или: newgrp docker
docker compose version
```

### 3.3. Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

Порт **8000 наружу не открывайте** — к нему обращается только reverse proxy на `127.0.0.1`.

### 3.4. Каталог приложения

```bash
sudo mkdir -p /opt/exam_tests
sudo chown "$USER:$USER" /opt/exam_tests
cd /opt/exam_tests
```

---

## 4. Клонирование репозитория

```bash
cd /opt/exam_tests
git clone <URL-репозитория> .
git checkout main   # или нужный release/tag
```

Структура, важная для деплоя:

```
exam_tests/
├── docker-compose.prod.yml   # production-стек
├── Dockerfile                # сборка backend + frontend/dist
├── .env.example              # шаблон переменных
├── alembic/                  # миграции БД
├── scripts/
│   ├── deploy.sh             # build + up + healthcheck
│   ├── migrate.sh            # alembic upgrade head
│   └── docker-entrypoint.sh  # миграции при старте контейнера
└── frontend/                 # исходники UI (собираются в образ)
```

---

## 5. Переменные окружения

### 5.1. Создание `.env`

```bash
cd /opt/exam_tests
cp .env.example .env
chmod 600 .env
```

Docker Compose автоматически подхватывает `.env` из корня проекта.

### 5.2. Обязательные значения для production

```bash
# Сгенерировать секрет сессий (минимум 32 байта в hex)
openssl rand -hex 32

# Сгенерировать пароль PostgreSQL
openssl rand -base64 24
```

Пример `.env` для production:

```env
# Пароль PostgreSQL (используется и контейнером db, и DATABASE_URL backend)
POSTGRES_PASSWORD=<сильный-пароль>

# Секрет подписи cookie-сессий — ОБЯЗАТЕЛЕН для docker-compose.prod.yml
SECRET_KEY=<результат openssl rand -hex 32>

# Публичный URL сайта (через HTTPS). Одного origin достаточно, если UI и API на одном домене.
CORS_ORIGINS=https://exam.example.com

# Порт, на котором слушает backend на хосте (за reverse proxy)
APP_PORT=8000

# Остальное задаётся в docker-compose.prod.yml, но можно переопределить:
RATE_LIMIT_ENABLED=true
BCRYPT_ROUNDS=12
CACHE_TTL_SECONDS=300
TEST_LIST_CACHE_TTL_SECONDS=3600
LOGIN_RATE_LIMIT_ATTEMPTS=5
LOGIN_RATE_LIMIT_WINDOW_SECONDS=300
EXPORT_TASK_TTL_SECONDS=3600
```

`DATABASE_URL` в `.env` для Docker **не обязателен** — он собирается в `docker-compose.prod.yml` из `POSTGRES_PASSWORD`.  
Для ручного запуска `migrate.sh` с хоста задайте:

```env
DATABASE_URL=postgresql+psycopg://postgres:<POSTGRES_PASSWORD>@127.0.0.1:5432/exam_tests
```

(порт 5432 понадобится только если вы временно пробросите PostgreSQL наружу для администрирования.)

### 5.3. Полная таблица переменных

| Переменная | Production | Описание |
|------------|------------|----------|
| `POSTGRES_PASSWORD` | **обязательно** | Пароль пользователя `postgres` в контейнере БД |
| `SECRET_KEY` | **обязательно** | Ключ подписи сессий; без него `docker compose` не стартует |
| `DATABASE_URL` | в compose | `postgresql+psycopg://postgres:…@db:5432/exam_tests` |
| `CORS_ORIGINS` | HTTPS-домен | Список через запятую; при одном домене — один URL |
| `SESSION_COOKIE_SECURE` | `true` | Cookie только по HTTPS (задано в prod compose) |
| `SESSION_COOKIE_HTTPONLY` | `true` | Защита от XSS |
| `SESSION_COOKIE_SAMESITE` | `lax` | Баланс CSRF и UX |
| `REDIS_URL` | `redis://redis:6379/0` | Rate limit и async export |
| `RATE_LIMIT_ENABLED` | `true` | HTTP rate limit через Redis |
| `RATE_LIMIT_REQUESTS` | `120` | Запросов на IP за окно |
| `RATE_LIMIT_WINDOW_SECONDS` | `60` | Окно rate limit |
| `AUTO_CREATE_SCHEMA` | `false` | Не использовать `create_all` |
| `RUN_MIGRATIONS` | `true` | Alembic при старте backend |
| `BCRYPT_ROUNDS` | `12` | Стоимость хэширования паролей |
| `CACHE_TTL_SECONDS` | `300` | In-memory кэш сервисов |
| `TEST_LIST_CACHE_TTL_SECONDS` | `3600` | Кэш списка тестов |
| `LOGIN_RATE_LIMIT_*` | см. `.env.example` | Защита от брутфорса логина |
| `EXPORT_TASK_TTL_SECONDS` | `3600` | TTL задач экспорта PDF/CSV в Redis |
| `APP_PORT` | `8000` | Проброс порта backend на хост |

---

## 6. База данных PostgreSQL

### 6.1. Встроенная БД (рекомендуется)

В `docker-compose.prod.yml` сервис `db`:

- образ `postgres:16`;
- база `exam_tests`, пользователь `postgres`;
- данные в именованном томе **`db_data`** (переживают перезапуск контейнеров).

При **первом** `docker compose up` PostgreSQL инициализирует кластер в томе. Backend после старта БД применяет миграции Alembic.

Проверить, что том создан:

```bash
docker volume ls | grep db_data
```

### 6.2. Подключение к БД для администрирования

```bash
docker compose -f docker-compose.prod.yml exec db \
  psql -U postgres -d exam_tests
```

Полезные команды в `psql`:

```sql
\dt                    -- список таблиц
SELECT id, username, role FROM users;
\q
```

### 6.3. Внешняя PostgreSQL (опционально)

Если БД на отдельном сервере (managed PostgreSQL, Patroni и т.п.):

1. Удалите или закомментируйте сервис `db` в отдельном override-файле.
2. Задайте `DATABASE_URL` на backend, укажите хост внешней БД.
3. Создайте пустую базу `exam_tests` и пользователя с правами DDL/DML.
4. Запустите миграции: `./scripts/migrate.sh` или старт backend с `RUN_MIGRATIONS=true`.

Формат URL: `postgresql+psycopg://user:password@host:5432/exam_tests`

---

## 7. Redis

В production Redis **обязателен** для:

- HTTP rate limiting (`RATE_LIMIT_ENABLED=true`);
- хранения состояния асинхронных export-задач (PDF/CSV).

Сервис `redis` в compose не требует отдельной настройки. Данные в Redis **эфемерны** — при перезапуске теряются незавершённые export-задачи, это нормально.

---

## 8. Первый деплой (пошагово)

Выполняйте из `/opt/exam_tests` после настройки `.env`.

### Шаг 1. Сборка образа

```bash
export SECRET_KEY="$(grep ^SECRET_KEY= .env | cut -d= -f2-)"
docker compose -f docker-compose.prod.yml build backend
```

Сборка включает `npm run build` для frontend и установку Python-зависимостей. Занимает несколько минут.

### Шаг 2. Запуск стека

```bash
docker compose -f docker-compose.prod.yml up -d
```

Поднимутся три сервиса: `db`, `redis`, `backend`.

### Шаг 3. Контроль миграций

```bash
docker compose -f docker-compose.prod.yml logs -f backend
```

Ожидаемые строки:

```
==> Running Alembic migrations
INFO  [alembic.runtime.migration] Running upgrade ... -> head
```

### Шаг 4. Healthcheck

```bash
curl -sf http://127.0.0.1:8000/api/health
# {"status":"ok"}
```

### Шаг 5. Проверка UI

```bash
curl -sI http://127.0.0.1:8000/ | head -5
```

Должен вернуться `200` и `Content-Type` HTML.

### Шаг 6. Скрипт `deploy.sh`

```bash
./scripts/deploy.sh
```

Скрипт делает `build`, `up -d` и ждёт `/api/health`. Подхватывает `.env` (в т.ч. `APP_PORT`, `SECRET_KEY`).  
При провале healthcheck контейнеры **остаются запущенными**, тома **не удаляются** — можно смотреть логи и чинить конфигурацию.

---

## 9. Миграции схемы (Alembic)

### 9.1. Автоматически при старте

Entrypoint `scripts/docker-entrypoint.sh`:

- при `RUN_MIGRATIONS=true` и `AUTO_CREATE_SCHEMA=false` выполняет `alembic upgrade head`;
- при ошибке на legacy-БД пробует `alembic stamp 001_initial` и повторный upgrade.

### 9.2. Вручную

Из корня проекта на сервере (нужен `DATABASE_URL`):

```bash
./scripts/migrate.sh
```

Или внутри контейнера:

```bash
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### 9.3. Перед миграциями на живой БД — бэкап

См. [раздел 13](#13-резервное-копирование-и-восстановление).

### 9.4. История миграций

Файлы: `alembic/versions/` (`001_initial_schema.py` … `012_wiki_pages.py`).

```bash
docker compose -f docker-compose.prod.yml exec backend alembic history
docker compose -f docker-compose.prod.yml exec backend alembic current
```

---

## 10. Первый администратор

### 10.1. Регистрация через UI

1. Откройте сайт (пока `http://IP:8000` или уже HTTPS через proxy).
2. Зарегистрируйте пользователя (роль по умолчанию — `kot`).

### 10.2. Назначение роли admin через SQL

```bash
docker compose -f docker-compose.prod.yml exec db psql -U postgres -d exam_tests -c \
  "UPDATE users SET role = 'admin' WHERE username = 'ваш_логин';"
```

Роли: `admin`, `ezh`, `kot` (см. README и `docs/BUSINESS_RULES.md`).

### 10.3. Назначение через API (если уже есть admin)

```bash
# после логина, cookie в cookies.txt
CSRF=$(curl -s -b cookies.txt -c cookies.txt https://exam.example.com/api/auth/csrf | jq -r .csrf_token)
curl -s -b cookies.txt -c cookies.txt \
  -X PUT "https://exam.example.com/api/admin/users/2/role" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: $CSRF" \
  -d '{"role":"admin"}'
```

---

## 11. HTTPS и reverse proxy

Backend слушает HTTP на `127.0.0.1:8000`. TLS завершается на reverse proxy.  
В production задано `SESSION_COOKIE_SECURE=true` — пользователи должны заходить **только по HTTPS**.

`CORS_ORIGINS` должен совпадать с публичным URL, например `https://exam.example.com`.

### 11.1. Nginx + Let's Encrypt (certbot)

Установка:

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

Файл `/etc/nginx/sites-available/exam_tests`:

```nginx
server {
    listen 80;
    server_name exam.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name exam.example.com;

    # certbot заполнит ssl_certificate после: certbot --nginx -d exam.example.com
    ssl_certificate     /etc/letsencrypt/live/exam.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/exam.example.com/privkey.pem;

    client_max_body_size 20m;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }
}
```

Активация:

```bash
sudo ln -s /etc/nginx/sites-available/exam_tests /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d exam.example.com
```

Автообновление сертификата: `certbot renew` (обычно через systemd timer).

### 11.2. Caddy (альтернатива)

`/etc/caddy/Caddyfile`:

```caddy
exam.example.com {
    reverse_proxy 127.0.0.1:8000
}
```

Caddy сам получит сертификат Let's Encrypt.

### 11.3. Проброс порта 8000

В `docker-compose.prod.yml` backend публикует `${APP_PORT:-8000}:8000`.  
Для production достаточно bind на localhost — при необходимости замените строку ports на:

```yaml
ports:
  - "127.0.0.1:${APP_PORT:-8000}:8000"
```

(правка в локальной копии compose или override-файле `docker-compose.override.yml`.)

---

## 12. Проверка после деплоя

Чек-лист:

| # | Проверка | Команда / действие |
|---|----------|-------------------|
| 1 | Health API | `curl -sf https://exam.example.com/api/health` |
| 2 | Главная страница | Открыть `/` в браузере, нет белого экрана |
| 3 | CSRF | `GET /api/auth/csrf` возвращает токен |
| 4 | Регистрация / вход | Создать пользователя, войти |
| 5 | Админ | SQL или API — роль `admin` |
| 6 | Список тестов | Раздел тестов в личном кабинете |
| 7 | Cookie | В DevTools: `exam_session`, `Secure`, `HttpOnly` |
| 8 | OpenAPI | `https://exam.example.com/docs` (ограничьте доступ на prod при желании) |

Логи при ошибках:

```bash
docker compose -f docker-compose.prod.yml logs --tail=200 backend
docker compose -f docker-compose.prod.yml ps
```

---

## 13. Резервное копирование и восстановление

### 13.1. Создание бэкапа

**Перед каждым обновлением с миграциями** — обязательно.

```bash
BACKUP_DIR=/opt/exam_tests/backups
mkdir -p "$BACKUP_DIR"
STAMP=$(date +%Y%m%d_%H%M%S)

docker compose -f docker-compose.prod.yml exec -T db \
  pg_dump -U postgres -Fc exam_tests > "$BACKUP_DIR/exam_tests_${STAMP}.dump"

ls -lh "$BACKUP_DIR"
```

Формат `-Fc` (custom) поддерживает параллельное восстановление и сжатие.

### 13.2. Восстановление

```bash
# остановить backend, чтобы не было записей во время restore
docker compose -f docker-compose.prod.yml stop backend

docker compose -f docker-compose.prod.yml exec -T db \
  pg_restore -U postgres -d exam_tests --clean --if-exists < backups/exam_tests_YYYYMMDD.dump

docker compose -f docker-compose.prod.yml start backend
```

На **пустую** базу иногда проще:

```bash
docker compose -f docker-compose.prod.yml exec -T db dropdb -U postgres exam_tests
docker compose -f docker-compose.prod.yml exec -T db createdb -U postgres exam_tests
docker compose -f docker-compose.prod.yml exec -T db \
  pg_restore -U postgres -d exam_tests < backups/exam_tests_YYYYMMDD.dump
```

### 13.3. Автоматизация (cron)

```bash
crontab -e
```

```cron
0 3 * * * cd /opt/exam_tests && docker compose -f docker-compose.prod.yml exec -T db pg_dump -U postgres -Fc exam_tests > /opt/exam_tests/backups/nightly_$(date +\%Y\%m\%d).dump
```

Храните копии off-site (S3, другой сервер).

### 13.4. Бэкап тома Docker (дополнительно)

```bash
docker run --rm -v exam_tests_db_data:/data -v /opt/exam_tests/backups:/backup alpine \
  tar czf /backup/db_volume_$(date +%Y%m%d).tar.gz -C /data .
```

Имя тома уточните: `docker volume ls`.

---

## 14. Обновление версии

```bash
cd /opt/exam_tests

# 1. Бэкап БД (см. выше)

# 2. Новый код
git fetch origin
git checkout main
git pull

# 3. Пересборка и перезапуск
docker compose -f docker-compose.prod.yml build backend
docker compose -f docker-compose.prod.yml up -d

# 4. Миграции применятся при старте backend; проверка:
docker compose -f docker-compose.prod.yml logs backend | tail -30
curl -sf http://127.0.0.1:8000/api/health
```

Образ можно тегировать для отката:

```bash
docker compose -f docker-compose.prod.yml build backend
docker tag exam_tests-backend:latest exam_tests-backend:$(git rev-parse --short HEAD)
```

---

## 15. Откат

### 15.1. Откат приложения (код/образ)

```bash
git checkout <предыдущий-commit-или-tag>
docker compose -f docker-compose.prod.yml build backend
docker compose -f docker-compose.prod.yml up -d
```

Или используйте сохранённый тег образа.

### 15.2. Откат миграции Alembic

Только если новая миграция обратима и вы понимаете последствия:

```bash
docker compose -f docker-compose.prod.yml exec backend alembic downgrade -1
```

При серьёзных проблемах надёжнее **восстановить бэкап БД** (раздел 13).

### 15.3. Полная остановка стека

```bash
docker compose -f docker-compose.prod.yml down
# БЕЗ -v — данные БД сохранятся
```

**Никогда не используйте `down -v` на production**, если не хотите уничтожить базу.

---

## 16. Мониторинг и логи

```bash
# статус контейнеров
docker compose -f docker-compose.prod.yml ps

# логи backend в реальном времени
docker compose -f docker-compose.prod.yml logs -f backend

# использование ресурсов
docker stats

# место на диске (том БД растёт с попытками и протоколами)
df -h
docker system df
```

Рекомендации:

- настроить алерт на недоступность `https://…/api/health` (Uptime Kuma, Prometheus blackbox и т.п.);
- ротировать логи Docker (`/etc/docker/daemon.json` → `log-driver`, `max-size`);
- следить за заполнением диска томом `db_data`.

Correlation ID: ответы API могут содержать заголовок `X-Correlation-ID` для поиска в логах.

---

## 17. Типичные проблемы

| Симптом | Вероятная причина | Решение |
|---------|-------------------|---------|
| `SECRET_KEY: set SECRET_KEY` | Нет переменной в `.env` | Задать `SECRET_KEY`, перезапустить compose |
| `502 Bad Gateway` от Nginx | Backend не запущен | `docker compose ps`, `logs backend` |
| Белый экран на `/` | Нет `frontend/dist` в образе | `docker compose build --no-cache backend` |
| `401` / сессия не держится | HTTP вместо HTTPS при `SESSION_COOKIE_SECURE=true` | Настроить TLS; cookie только по HTTPS |
| CORS ошибки в браузере | Неверный `CORS_ORIGINS` | Указать точный origin с `https://` |
| Миграции падают | Старая/битая схема | Бэкап → `alembic current` → при необходимости stamp/restore |
| Rate limit / export не работают | Redis недоступен | `docker compose logs redis`, проверить `REDIS_URL` |
| `no configuration file provided` | Запуск не из корня репо | `cd /opt/exam_tests` |
| Health OK, но UI 404 | Старый образ без frontend | Пересобрать backend |
| Healthcheck failed в deploy.sh | Backend не поднялся / неверный порт | `docker compose logs backend`; проверить `.env` и `APP_PORT` |

---

## 18. Staging

Используйте тот же `docker-compose.prod.yml` на отдельном хосте или поддомене:

```bash
export SECRET_KEY=$(openssl rand -hex 32)
# .env: CORS_ORIGINS=https://staging.example.com, POSTGRES_PASSWORD=...

docker compose -f docker-compose.prod.yml build backend
docker compose -f docker-compose.prod.yml up -d
curl -sf https://staging.example.com/api/health
```

Отличия от production: отдельные секреты, отдельный том `db_data`, можно ослабить rate limit для тестов.

---

## 19. Альтернатива: без Docker

Если PostgreSQL и Redis уже установлены на сервере:

```bash
cd /opt/exam_tests
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# DATABASE_URL, REDIS_URL, SECRET_KEY, AUTO_CREATE_SCHEMA=false, RUN_MIGRATIONS=true

cd frontend && npm ci && npm run build && cd ..
alembic upgrade head

uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Для production лучше process manager (systemd) и reverse proxy:

```ini
# /etc/systemd/system/exam-tests.service
[Unit]
Description=Exam Tests API
After=network.target postgresql.service redis.service

[Service]
User=exam
WorkingDirectory=/opt/exam_tests
EnvironmentFile=/opt/exam_tests/.env
ExecStart=/opt/exam_tests/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Docker-подход предпочтительнее: воспроизводимая сборка frontend, одинаковые версии Python/Node, изоляция PostgreSQL.

---

## Краткая шпаргалка

```bash
# Первый запуск
cp .env.example .env && nano .env
docker compose -f docker-compose.prod.yml build backend
docker compose -f docker-compose.prod.yml up -d
curl -sf http://127.0.0.1:8000/api/health

# Админ
docker compose -f docker-compose.prod.yml exec db psql -U postgres -d exam_tests \
  -c "UPDATE users SET role = 'admin' WHERE username = 'admin';"

# Бэкап
docker compose -f docker-compose.prod.yml exec -T db pg_dump -U postgres -Fc exam_tests > backup.dump

# Обновление
git pull && docker compose -f docker-compose.prod.yml build backend && docker compose -f docker-compose.prod.yml up -d
```
