# Деплой

## Staging

```bash
export SECRET_KEY=$(openssl rand -hex 32)
export DATABASE_URL=postgresql+psycopg://postgres:pass@db:5432/exam_tests
export REDIS_URL=redis://redis:6379/0
export AUTO_CREATE_SCHEMA=false
export RUN_MIGRATIONS=true
export CORS_ORIGINS=https://staging.example.com

docker compose -f docker-compose.prod.yml build backend
docker compose -f docker-compose.prod.yml up -d
./scripts/migrate.sh   # при необходимости вручную до entrypoint
```

Проверка: `curl -sf https://staging.example.com/api/health`

## Production

1. **Бэкап БД** перед миграциями:
   ```bash
   pg_dump "$DATABASE_URL" -Fc -f backup_$(date +%Y%m%d).dump
   ```
2. `AUTO_CREATE_SCHEMA=false`, `RUN_MIGRATIONS=true`
3. `SESSION_COOKIE_SECURE=true`, сильный `SECRET_KEY`
4. `RATE_LIMIT_ENABLED=true`, `REDIS_URL` обязателен для export и rate limit
5. `./scripts/deploy.sh` — smoke healthcheck; при провале — `down -v`

### Откат

```bash
docker compose -f docker-compose.prod.yml down
# восстановить предыдущий образ / git tag
docker compose -f docker-compose.prod.yml up -d
# при откате схемы: alembic downgrade -1
```

### После деплоя

- Очистка кэша приложения: перезапуск backend или `invalidate_cache` через redeploy
- Уведомление команды: статус health + версия образа (`APP_VERSION` в CI при необходимости)

## Переменные окружения

См. `.env.example`.
