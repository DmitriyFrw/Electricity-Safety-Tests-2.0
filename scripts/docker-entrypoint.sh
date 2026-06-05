#!/usr/bin/env bash
set -euo pipefail

cd /app

_run_alembic() {
  echo "==> Running Alembic migrations"
  if alembic upgrade head; then
    return 0
  fi
  echo "==> Alembic upgrade failed; stamping 001_initial for legacy create_all database"
  alembic stamp 001_initial
  alembic upgrade head
}

if [[ "${RUN_MIGRATIONS:-true}" == "true" ]] && [[ "${AUTO_CREATE_SCHEMA:-false}" != "true" ]]; then
  _run_alembic
elif [[ "${AUTO_CREATE_SCHEMA:-false}" == "true" ]]; then
  _run_alembic || echo "==> Alembic skipped (will rely on create_all + manual migrate if needed)"
  echo "==> AUTO_CREATE_SCHEMA=true (create_all on app startup)"
else
  echo "==> RUN_MIGRATIONS=false, skipping Alembic"
fi

exec "$@"
