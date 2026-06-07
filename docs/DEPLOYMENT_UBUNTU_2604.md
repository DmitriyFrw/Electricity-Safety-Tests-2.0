# Развёртывание на Ubuntu 26.04

Подробное руководство по установке **PostgreSQL**, **Redis** и сервера платформы **Развивайся** (FastAPI + React) на чистой **Ubuntu 26.04 LTS**.

Рекомендуемый способ — **Docker Compose** (`docker-compose.prod.yml`): один стек, воспроизводимая сборка, изоляция БД.  
Альтернатива — установка PostgreSQL и Redis «на железо» + systemd (раздел [12](#12-альтернатива-без-docker-native-стек)).

Общая документация: [DEPLOYMENT.md](DEPLOYMENT.md) · Docker dev: [DOCKER.md](DOCKER.md)

---

## Содержание

1. [Что будет развёрнуто](#1-что-будет-развёрнуто)
2. [Требования](#2-требования)
3. [Подготовка Ubuntu 26.04](#3-подготовка-ubuntu-2604)
4. [Установка Docker Engine](#4-установка-docker-engine)
5. [Клонирование проекта](#5-клонирование-проекта)
6. [Настройка переменных окружения](#6-настройка-переменных-окружения)
7. [База данных PostgreSQL (в Docker)](#7-база-данных-postgresql-в-docker)
8. [Redis (в Docker)](#8-redis-в-docker)
9. [Первый запуск backend + UI](#9-первый-запуск-backend--ui)
10. [Миграции Alembic](#10-миграции-alembic)
11. [HTTPS: Nginx + Let's Encrypt](#11-https-nginx--lets-encrypt)
12. [Первый администратор](#12-первый-администратор)
13. [Проверка после деплоя](#13-проверка-после-деплоя)
14. [Резервное копирование БД](#14-резервное-копирование-бд)
15. [Обновление и откат](#15-обновление-и-откат)
16. [Мониторинг и логи](#16-мониторинг-и-логи)
17. [Типичные проблемы](#17-типичные-проблемы)
18. [Альтернатива без Docker (native стек)](#18-альтернатива-без-docker-native-стек)
19. [Шпаргалка команд](#19-шпаргалка-команд)

---

## 1. Что будет развёрнуто

```
Интернет ──HTTPS──► Nginx/Caddy (:443)
                         │
                         ▼ HTTP 127.0.0.1:8000
                    ┌────────────────────────────┐
                    │  backend (контейнер)       │
                    │  • FastAPI /api/*          │
                    │  • React SPA frontend/dist │
                    │  • uvicorn                 │
                    └───────┬──────────┬─────────┘
                            │          │
                     PostgreSQL 16   Redis 7
                     (том db_data)   (rate limit, export)
```

| Компонент | Назначение |
|-----------|------------|
| **PostgreSQL 16** | Пользователи, тесты, попытки, протоколы, вики |
| **Redis 7** | HTTP rate limit, async export PDF/CSV |
| **backend** | API + собранный frontend (один процесс) |
| **Nginx** | TLS, reverse proxy (на хосте, не в Docker) |

В production PostgreSQL и Redis **не публикуются наружу** — только внутренняя Docker-сеть.

---

## 2. Требования

### Сервер

| Параметр | Минимум | Рекомендуется |
|----------|---------|---------------|
| ОС | **Ubuntu 26.04 LTS** | Ubuntu 26.04 LTS |
| CPU | 2 vCPU | 4 vCPU |
| RAM | 2 GB | 4 GB |
| Диск | 25 GB SSD | 50+ GB SSD |
| Сеть | Публичный IPv4 или IPv6 | Статический IP, DNS A-запись |

### Порты (firewall)

| Порт | Куда | Комментарий |
|------|------|-------------|
| **22** | SSH | Ограничьте по IP, если возможно |
| **80** | Nginx | HTTP → редирект на HTTPS |
| **443** | Nginx | Публичный доступ к сайту |
| **8000** | localhost | Backend; **не открывать в интернет** |
| 5432, 6379 | — | **Не открывать** (БД и Redis только внутри Docker) |

### Доменное имя

Для production с HTTPS нужен DNS, например:

```
exam.example.com  →  A  →  IP_вашего_сервера
```

---

## 3. Подготовка Ubuntu 26.04

Подключитесь по SSH под пользователем с `sudo`.

### 3.1. Обновление системы и локаль

```bash
sudo apt update && sudo apt full-upgrade -y
sudo timedatectl set-timezone Europe/Moscow   # или ваш часовой пояс
timedatectl status
```

### 3.2. Базовые пакеты

```bash
sudo apt install -y \
  ca-certificates curl gnupg git ufw \
  openssl jq unzip htop
```

### 3.3. Отдельный пользователь для приложения (рекомендуется)

```bash
sudo adduser --disabled-password --gecos "" exam
sudo usermod -aG sudo exam   # опционально, если нужен sudo
```

Дальнейшие команды можно выполнять от `exam` или от вашего пользователя — в гайде используется `/opt/exam_tests`.

### 3.4. Firewall (UFW)

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status verbose
```

### 3.5. Каталог приложения

```bash
sudo mkdir -p /opt/exam_tests
sudo mkdir -p /opt/exam_tests/backups
sudo chown -R "$USER:$USER" /opt/exam_tests
cd /opt/exam_tests
```

### 3.6. Swap (если RAM ≤ 2 GB)

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
free -h
```

---

## 4. Установка Docker Engine

На Ubuntu 26.04 используйте официальный репозиторий Docker. Кодовое имя дистрибутива подставится автоматически из `/etc/os-release`.

### 4.1. Репозиторий и пакеты

```bash
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

### 4.2. Права и автозапуск

```bash
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
newgrp docker   # или перелогиньтесь по SSH
```

### 4.3. Проверка

```bash
docker --version
docker compose version
docker run --rm hello-world
```

Ожидается успешный вывод `Hello from Docker!`.

### 4.4. (Опционально) Ограничение логов Docker

```bash
sudo tee /etc/docker/daemon.json <<'EOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "50m",
    "max-file": "3"
  }
}
EOF
sudo systemctl restart docker
```

---

## 5. Клонирование проекта

```bash
cd /opt/exam_tests
git clone <URL-вашего-репозитория> .
git checkout main    # или release/tag
git log -1 --oneline
```

Структура, важная для деплоя:

```
exam_tests/
├── docker-compose.prod.yml   # production: db + redis + backend
├── compose.yaml              # dev-стек (не для production)
├── Dockerfile                # сборка backend + frontend/dist
├── .env.example
├── alembic/versions/         # миграции 001 … 012
├── scripts/
│   ├── deploy.sh
│   ├── migrate.sh
│   └── docker-entrypoint.sh
└── frontend/                 # исходники UI (собираются в образ)
```

---

## 6. Настройка переменных окружения

### 6.1. Создание `.env`

```bash
cd /opt/exam_tests
cp .env.example .env
chmod 600 .env
```

### 6.2. Генерация секретов

```bash
# Секрет сессий (cookie)
openssl rand -hex 32

# Пароль PostgreSQL
openssl rand -base64 24
```

Сохраните значения — они понадобятся в `.env`.

### 6.3. Пример `.env` для production

Отредактируйте `/opt/exam_tests/.env`:

```env
# === ОБЯЗАТЕЛЬНО ===
POSTGRES_PASSWORD=<результат openssl rand -base64 24>
SECRET_KEY=<результат openssl rand -hex 32>

# Публичный URL сайта (точно с https://)
CORS_ORIGINS=https://exam.example.com

# Порт backend на хосте (за Nginx)
APP_PORT=8000

# === ОПЦИОНАЛЬНО (есть разумные значения по умолчанию в compose) ===
RATE_LIMIT_ENABLED=true
BCRYPT_ROUNDS=12
CACHE_TTL_SECONDS=300
TEST_LIST_CACHE_TTL_SECONDS=3600
LOGIN_RATE_LIMIT_ATTEMPTS=5
LOGIN_RATE_LIMIT_WINDOW_SECONDS=300
EXPORT_TASK_TTL_SECONDS=3600
```

**Важно:**

- `DATABASE_URL` для Docker **задаётся в `docker-compose.prod.yml`** — вручную в `.env` не нужен, если используете встроенный контейнер `db`.
- `SECRET_KEY` **обязателен** — без него `docker compose` не запустит backend (`${SECRET_KEY:?set SECRET_KEY}`).
- `CORS_ORIGINS` должен **точно совпадать** с URL в браузере (схема + домен, без слэша в конце).

### 6.4. Таблица переменных production

| Переменная | Где задаётся | Production |
|------------|--------------|------------|
| `POSTGRES_PASSWORD` | `.env` | Сильный пароль |
| `SECRET_KEY` | `.env` | ≥ 32 байт случайных |
| `CORS_ORIGINS` | `.env` | `https://ваш-домен` |
| `DATABASE_URL` | compose | `postgresql+psycopg://postgres:…@db:5432/exam_tests` |
| `REDIS_URL` | compose | `redis://redis:6379/0` |
| `SESSION_COOKIE_SECURE` | compose | `true` |
| `AUTO_CREATE_SCHEMA` | compose | `false` |
| `RUN_MIGRATIONS` | compose | `true` |
| `RATE_LIMIT_ENABLED` | `.env`/compose | `true` |

---

## 7. База данных PostgreSQL (в Docker)

### 7.1. Как это работает

Сервис `db` в `docker-compose.prod.yml`:

- образ **PostgreSQL 16**;
- база **`exam_tests`**, пользователь **`postgres`**;
- пароль из **`POSTGRES_PASSWORD`** в `.env`;
- данные в именованном томе **`db_data`** (переживают перезапуск и `docker compose down` без `-v`).

При первом `docker compose up` PostgreSQL инициализирует кластер в томе. Backend при старте выполняет **Alembic upgrade head**.

### 7.2. Проверка тома после первого запуска

```bash
docker volume ls | grep db_data
docker volume inspect exam_tests_db_data
```

### 7.3. Подключение к БД (администрирование)

```bash
cd /opt/exam_tests
docker compose -f docker-compose.prod.yml exec db \
  psql -U postgres -d exam_tests
```

Полезные команды в `psql`:

```sql
\dt                              -- список таблиц
\d users                         -- структура таблицы
SELECT id, username, role FROM users;
SELECT COUNT(*) FROM tests;
\q
```

### 7.4. Ожидаемые таблицы после миграций

После `alembic upgrade head` (001 → 012):

- `users`, `tests`, `tickets`, `questions`
- `attempts`, `ticket_attempts`, `user_answers`, `signed_protocols`
- `wiki_pages`, `wiki_attachments`
- `alembic_version`

Проверка версии миграции:

```bash
docker compose -f docker-compose.prod.yml exec backend alembic current
```

### 7.5. Внешняя PostgreSQL (отдельный сервер)

Если БД на managed PostgreSQL или другом хосте:

1. Создайте пустую базу `exam_tests` и пользователя с правами DDL/DML.
2. В override-файле отключите сервис `db` или не поднимайте его.
3. Задайте `DATABASE_URL` для backend:

   ```env
   DATABASE_URL=postgresql+psycopg://user:password@db-host:5432/exam_tests
   ```

4. Запустите миграции вручную (раздел [10](#10-миграции-alembic)).

---

## 8. Redis (в Docker)

Redis обязателен в production для:

- HTTP rate limiting (`RATE_LIMIT_ENABLED=true`);
- хранения async export-задач (PDF/CSV).

Отдельная настройка не требуется. Данные в Redis **эфемерны** — при перезапуске теряются незавершённые export-задачи, это нормально.

Проверка:

```bash
docker compose -f docker-compose.prod.yml exec redis redis-cli ping
# PONG
```

---

## 9. Первый запуск backend + UI

Все команды из `/opt/exam_tests`, файл `.env` уже настроен.

### Шаг 1. Сборка образа backend

Сборка включает `npm run build` для frontend и установку Python-зависимостей (5–15 минут):

```bash
cd /opt/exam_tests
docker compose -f docker-compose.prod.yml build backend
```

При проблемах с кэшем:

```bash
docker compose -f docker-compose.prod.yml build --no-cache backend
```

### Шаг 2. Запуск стека

```bash
docker compose -f docker-compose.prod.yml up -d
```

Поднимутся три сервиса: `db`, `redis`, `backend`.

### Шаг 3. Статус контейнеров

```bash
docker compose -f docker-compose.prod.yml ps
```

Все сервисы должны быть `running`. Backend может несколько секунд ждать готовности PostgreSQL.

### Шаг 4. Логи backend (миграции)

```bash
docker compose -f docker-compose.prod.yml logs -f backend
```

Ожидаемые строки:

```
==> Running Alembic migrations
INFO  [alembic.runtime.migration] Running upgrade ... -> 012_wiki_pages
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Шаг 5. Healthcheck

```bash
curl -sf http://127.0.0.1:8000/api/health
```

Ответ: `{"status":"ok"}`

### Шаг 6. Проверка UI

```bash
curl -sI http://127.0.0.1:8000/ | head -5
```

Должен быть `HTTP/1.1 200` и HTML.

### Шаг 7. Скрипт автоматического деплоя

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

Скрипт: `build` → `up -d` → ожидание `/api/health`.  
При провале healthcheck контейнеры **остаются запущенными**, тома **не удаляются**.

### Шаг 8. Привязка backend только к localhost (рекомендуется)

По умолчанию порт `8000` слушает на всех интерфейсах. Для production создайте override:

```bash
cat > docker-compose.override.yml <<'EOF'
services:
  backend:
    ports:
      - "127.0.0.1:${APP_PORT:-8000}:8000"
EOF
```

Перезапуск:

```bash
docker compose -f docker-compose.prod.yml up -d
```

---

## 10. Миграции Alembic

### 10.1. Автоматически при старте контейнера

`scripts/docker-entrypoint.sh` при `RUN_MIGRATIONS=true` и `AUTO_CREATE_SCHEMA=false`:

1. выполняет `alembic upgrade head`;
2. при ошибке на legacy-БД пробует `alembic stamp 001_initial` и повтор.

### 10.2. Вручную

```bash
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

Или с хоста (если настроен `DATABASE_URL` на localhost):

```bash
./scripts/migrate.sh
```

### 10.3. История миграций

| Revision | Описание |
|----------|----------|
| 001 | Начальная схема |
| 002 | business_unit у пользователя |
| 003 | title у билета |
| 004 | option_count у билета |
| 005 | random_ticket_order |
| 006–007 | Группы электробезопасности |
| 008 | published у теста |
| 009 | correct_indexes у вопроса |
| 010 | selected_indexes у ответа |
| 011 | option_count на уровне вопроса |
| 012 | wiki_pages, wiki_attachments |

```bash
docker compose -f docker-compose.prod.yml exec backend alembic history --verbose
docker compose -f docker-compose.prod.yml exec backend alembic current
```

### 10.4. Перед миграцией на живой БД

**Обязательно** сделайте бэкап (раздел [14](#14-резервное-копирование-бд)).

---

## 11. HTTPS: Nginx + Let's Encrypt

Backend отдаёт HTTP на `127.0.0.1:8000`. TLS завершается на Nginx.  
При `SESSION_COOKIE_SECURE=true` пользователи должны заходить **только по HTTPS**.

### 11.1. Установка Nginx и Certbot

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
sudo systemctl enable nginx
```

### 11.2. Конфигурация сайта

Замените `exam.example.com` на ваш домен.

```bash
sudo tee /etc/nginx/sites-available/exam_tests <<'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name exam.example.com;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name exam.example.com;

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
        proxy_connect_timeout 10s;
    }
}
EOF
```

### 11.3. Временный HTTP-only конфиг для получения сертификата

Перед первым запуском certbot SSL-блок может не работать. Упрощённый вариант:

```bash
sudo tee /etc/nginx/sites-available/exam_tests <<'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name exam.example.com;

    client_max_body_size 20m;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/exam_tests /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

### 11.4. Получение сертификата

```bash
sudo certbot --nginx -d exam.example.com
```

Certbot обновит конфиг Nginx и настроит HTTPS.

### 11.5. Автообновление сертификата

```bash
sudo certbot renew --dry-run
systemctl list-timers | grep certbot
```

### 11.6. Обновите CORS

В `.env`:

```env
CORS_ORIGINS=https://exam.example.com
```

Перезапуск backend:

```bash
docker compose -f docker-compose.prod.yml up -d backend
```

### 11.7. Альтернатива: Caddy

```bash
sudo apt install -y caddy
sudo tee /etc/caddy/Caddyfile <<'EOF'
exam.example.com {
    reverse_proxy 127.0.0.1:8000
}
EOF
sudo systemctl reload caddy
```

Caddy сам получит сертификат Let's Encrypt.

---

## 12. Первый администратор

### 12.1. Регистрация через UI

1. Откройте `https://exam.example.com`
2. Зарегистрируйте пользователя (роль по умолчанию — **kot**)

### 12.2. Назначение admin через SQL

```bash
docker compose -f docker-compose.prod.yml exec db psql -U postgres -d exam_tests -c \
  "UPDATE users SET role = 'admin' WHERE username = 'ваш_логин';"
```

Роли: `admin`, `ezh`, `kot`.

### 12.3. Проверка

```bash
docker compose -f docker-compose.prod.yml exec db psql -U postgres -d exam_tests -c \
  "SELECT id, username, role FROM users;"
```

---

## 13. Проверка после деплоя

| # | Проверка | Команда / действие |
|---|----------|-------------------|
| 1 | Health API | `curl -sf https://exam.example.com/api/health` |
| 2 | Главная | Открыть `/` — нет белого экрана |
| 3 | CSRF | `curl -s https://exam.example.com/api/auth/csrf` |
| 4 | Регистрация / вход | Создать пользователя, войти |
| 5 | Админ | Роль `admin` назначена |
| 6 | Личный кабинет | `/cabinet` открывается |
| 7 | Вики | `/wiki` — страницы (если созданы) |
| 8 | Cookie | DevTools: `Secure`, `HttpOnly` |
| 9 | Контейнеры | `docker compose -f docker-compose.prod.yml ps` |

Логи при ошибках:

```bash
docker compose -f docker-compose.prod.yml logs --tail=200 backend
docker compose -f docker-compose.prod.yml logs --tail=50 db redis
```

---

## 14. Резервное копирование БД

### 14.1. Ручной бэкап

**Перед каждым обновлением с миграциями.**

```bash
cd /opt/exam_tests
STAMP=$(date +%Y%m%d_%H%M%S)
docker compose -f docker-compose.prod.yml exec -T db \
  pg_dump -U postgres -Fc exam_tests > "backups/exam_tests_${STAMP}.dump"
ls -lh backups/
```

### 14.2. Восстановление

```bash
docker compose -f docker-compose.prod.yml stop backend

docker compose -f docker-compose.prod.yml exec -T db \
  pg_restore -U postgres -d exam_tests --clean --if-exists \
  < backups/exam_tests_YYYYMMDD_HHMMSS.dump

docker compose -f docker-compose.prod.yml start backend
```

### 14.3. Ежедневный cron

```bash
crontab -e
```

```cron
0 3 * * * cd /opt/exam_tests && docker compose -f docker-compose.prod.yml exec -T db pg_dump -U postgres -Fc exam_tests > /opt/exam_tests/backups/nightly_$(date +\%Y\%m\%d).dump 2>> /opt/exam_tests/backups/cron.log
```

Храните копии **off-site** (S3, другой сервер, объектное хранилище).

### 14.4. Бэкап вложений вики

Файлы вики лежат в контейнере: `app/static/wiki/`. При пересборке образа они **теряются**, если не смонтирован volume.

Для production добавьте в override:

```yaml
services:
  backend:
    volumes:
      - wiki_uploads:/app/app/static/wiki
volumes:
  wiki_uploads:
```

---

## 15. Обновление и откат

### 15.1. Обновление версии

```bash
cd /opt/exam_tests

# 1. Бэкап БД
docker compose -f docker-compose.prod.yml exec -T db \
  pg_dump -U postgres -Fc exam_tests > backups/pre_update_$(date +%Y%m%d).dump

# 2. Новый код
git fetch origin
git checkout main
git pull

# 3. Пересборка и перезапуск
docker compose -f docker-compose.prod.yml build backend
docker compose -f docker-compose.prod.yml up -d

# 4. Проверка
docker compose -f docker-compose.prod.yml logs backend | tail -40
curl -sf http://127.0.0.1:8000/api/health
```

### 15.2. Тег образа для отката

```bash
docker compose -f docker-compose.prod.yml build backend
docker tag exam_tests-backend:latest exam_tests-backend:$(git rev-parse --short HEAD)
```

### 15.3. Откат кода

```bash
git checkout <предыдущий-commit>
docker compose -f docker-compose.prod.yml build backend
docker compose -f docker-compose.prod.yml up -d
```

### 15.4. Откат миграции

Только если миграция обратима:

```bash
docker compose -f docker-compose.prod.yml exec backend alembic downgrade -1
```

При серьёзных проблемах — **восстановление из бэкапа** (раздел 14).

### 15.5. Остановка стека

```bash
docker compose -f docker-compose.prod.yml down
# БЕЗ -v — данные БД сохранятся
```

**Никогда не используйте `down -v` на production**, если не хотите уничтожить базу.

---

## 16. Мониторинг и логи

```bash
# Статус
docker compose -f docker-compose.prod.yml ps

# Логи в реальном времени
docker compose -f docker-compose.prod.yml logs -f backend

# Ресурсы
docker stats

# Диск
df -h
docker system df
du -sh /var/lib/docker/volumes/
```

Рекомендации:

- мониторинг `https://exam.example.com/api/health` (Uptime Kuma, Better Stack и т.п.);
- алерт при заполнении диска > 80%;
- в логах API ищите заголовок `X-Correlation-ID`.

---

## 17. Типичные проблемы

| Симптом | Причина | Решение |
|---------|---------|---------|
| `SECRET_KEY: set SECRET_KEY` | Нет в `.env` | Задать `SECRET_KEY`, перезапустить |
| `502 Bad Gateway` | Backend не запущен | `docker compose ps`, `logs backend` |
| Белый экран на `/` | Нет `frontend/dist` в образе | `build --no-cache backend` |
| Сессия не держится | HTTP вместо HTTPS | Nginx + `SESSION_COOKIE_SECURE=true` |
| CORS в браузере | Неверный `CORS_ORIGINS` | Точный `https://домен` |
| Миграции падают | Старая/битая схема | Бэкап → `alembic current` → restore |
| Rate limit не работает | Redis недоступен | `logs redis`, `redis-cli ping` |
| `Status code 204 must not have a response body` | Старая версия кода | Обновить репозиторий, пересобрать |
| Health OK, UI 404 | Старый образ | Пересобрать backend |
| Нет места на диске | Рост тома БД / логов | `docker system prune`, ротация логов, расширить диск |

---

## 18. Альтернатива без Docker (native стек)

Если PostgreSQL и Redis установлены **на Ubuntu 26.04** напрямую.

### 18.1. PostgreSQL 16

```bash
sudo apt install -y postgresql postgresql-contrib
sudo systemctl enable --now postgresql

sudo -u postgres psql <<'SQL'
CREATE USER exam_app WITH PASSWORD 'сильный-пароль';
CREATE DATABASE exam_tests OWNER exam_app;
GRANT ALL PRIVILEGES ON DATABASE exam_tests TO exam_app;
SQL
```

В `.env`:

```env
DATABASE_URL=postgresql+psycopg://exam_app:сильный-пароль@127.0.0.1:5432/exam_tests
```

### 18.2. Redis

```bash
sudo apt install -y redis-server
sudo systemctl enable --now redis-server
redis-cli ping
```

```env
REDIS_URL=redis://127.0.0.1:6379/0
RATE_LIMIT_ENABLED=true
```

### 18.3. Python и приложение

```bash
cd /opt/exam_tests
sudo apt install -y python3.12 python3.12-venv build-essential libpq-dev

python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

cd frontend
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
npm ci
npm run build
cd ..

cp .env.example .env
# SECRET_KEY, DATABASE_URL, REDIS_URL, CORS_ORIGINS
# AUTO_CREATE_SCHEMA=false, RUN_MIGRATIONS=true
# SESSION_COOKIE_SECURE=true

alembic upgrade head
```

### 18.4. Systemd unit

```bash
sudo tee /etc/systemd/system/exam-tests.service <<'EOF'
[Unit]
Description=Exam Tests (Развивайся) API
After=network.target postgresql.service redis-server.service
Wants=postgresql.service redis-server.service

[Service]
Type=simple
User=exam
Group=exam
WorkingDirectory=/opt/exam_tests
EnvironmentFile=/opt/exam_tests/.env
Environment=PYTHONPATH=/opt/exam_tests
ExecStart=/opt/exam_tests/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now exam-tests
sudo systemctl status exam-tests
curl -sf http://127.0.0.1:8000/api/health
```

Nginx настраивается так же, как в разделе [11](#11-https-nginx--lets-encrypt).

**Docker предпочтительнее:** одинаковые версии Python/Node, изолированная БД, проще обновления.

---

## 19. Шпаргалка команд

```bash
# === Первый деплой ===
cd /opt/exam_tests
cp .env.example .env && nano .env
docker compose -f docker-compose.prod.yml build backend
docker compose -f docker-compose.prod.yml up -d
curl -sf http://127.0.0.1:8000/api/health

# === Админ ===
docker compose -f docker-compose.prod.yml exec db psql -U postgres -d exam_tests \
  -c "UPDATE users SET role = 'admin' WHERE username = 'admin';"

# === Бэкап ===
docker compose -f docker-compose.prod.yml exec -T db \
  pg_dump -U postgres -Fc exam_tests > backups/backup.dump

# === Обновление ===
git pull
docker compose -f docker-compose.prod.yml build backend
docker compose -f docker-compose.prod.yml up -d

# === Логи ===
docker compose -f docker-compose.prod.yml logs -f backend

# === Миграции ===
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
docker compose -f docker-compose.prod.yml exec backend alembic current
```

---

*Документ актуален для Ubuntu 26.04 LTS и стека `docker-compose.prod.yml` (PostgreSQL 16, Redis 7, Python 3.12, Node 20).*
