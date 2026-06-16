#!/usr/bin/env bash
set -euo pipefail

cd /app

_require_database_url() {
  if [[ -n "${DATABASE_URL:-}" ]]; then
    return 0
  fi
  cat >&2 <<'EOF'
ERROR: DATABASE_URL is not set.

Pass it when starting the container, for example:
  -e DATABASE_URL=postgresql+psycopg://postgres:postgres@host.containers.internal:5432/exam_tests

Or use docker-compose.prod.yml (backend + db + redis).
To skip migrations: -e RUN_MIGRATIONS=false (app still needs DATABASE_URL at runtime).
EOF
  exit 1
}

_schema_has_users_table() {
  python - <<'PY'
import sys
from sqlalchemy import create_engine, inspect
from app.config import get_settings

url = get_settings().database_url
if not url:
    sys.exit(1)
engine = create_engine(url)
try:
    names = inspect(engine).get_table_names()
except Exception:
    sys.exit(1)
sys.exit(0 if "users" in names else 1)
PY
}

_run_alembic() {
  _require_database_url
  echo "==> Running Alembic migrations"
  if alembic upgrade head; then
    return 0
  fi
  if _schema_has_users_table; then
    echo "==> Legacy create_all database: stamp head, then retry upgrade"
    alembic stamp head
    alembic upgrade head
    return 0
  fi
  cat >&2 <<'EOF'
ERROR: Alembic upgrade failed on an empty or incomplete database.

If this is a fresh install, wipe the Postgres volume and retry:
  podman compose -f docker-compose.prod.yml down -v
  podman compose -f docker-compose.prod.yml up -d --build

Only one service should run migrations (backend). Set RUN_MIGRATIONS=false on export-worker.
EOF
  exit 1
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
