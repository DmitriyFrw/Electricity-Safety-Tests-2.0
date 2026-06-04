#!/usr/bin/env bash
set -euo pipefail

cd /app

if [[ "${RUN_MIGRATIONS:-true}" == "true" ]] && [[ "${AUTO_CREATE_SCHEMA:-false}" != "true" ]]; then
  echo "==> Running Alembic migrations"
  alembic upgrade head
elif [[ "${AUTO_CREATE_SCHEMA:-false}" == "true" ]]; then
  echo "==> AUTO_CREATE_SCHEMA=true, skipping Alembic (schema via create_all on startup)"
else
  echo "==> RUN_MIGRATIONS=false, skipping Alembic"
fi

exec "$@"
