#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"

echo "==> Building images"
docker compose -f "$COMPOSE_FILE" build backend

echo "==> Starting stack"
docker compose -f "$COMPOSE_FILE" up -d

echo "==> Waiting for health"
for i in $(seq 1 30); do
  if curl -sf "http://127.0.0.1:${APP_PORT:-8000}/api/health" >/dev/null; then
    echo "Deploy OK"
    exit 0
  fi
  sleep 2
done

echo "Health check failed"
docker compose -f "$COMPOSE_FILE" logs backend
docker compose -f "$COMPOSE_FILE" down -v
exit 1
