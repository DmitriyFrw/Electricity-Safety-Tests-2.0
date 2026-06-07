#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

HEALTH_URL="http://127.0.0.1:${APP_PORT:-8000}/api/health"

echo "==> Building images"
docker compose -f "$COMPOSE_FILE" build backend

echo "==> Starting stack"
docker compose -f "$COMPOSE_FILE" up -d

echo "==> Waiting for health ($HEALTH_URL)"
for i in $(seq 1 30); do
  if curl -sf "$HEALTH_URL" >/dev/null; then
    echo "Deploy OK"
    exit 0
  fi
  sleep 2
done

echo "Health check failed — stack left running for inspection (volumes not removed)" >&2
docker compose -f "$COMPOSE_FILE" logs --tail=100 backend
exit 1
