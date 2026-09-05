#!/usr/bin/env bash
# Fly release_command — run Alembic with explicit logs and hard timeouts.
# Prevents deploy hangs where the release machine never reaches "stopped".
set -euo pipefail

echo "fly_release_migrate: start $(date -u +%Y-%m-%dT%H:%M:%SZ)"

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "fly_release_migrate: ERROR — DATABASE_URL not set on release machine" >&2
  exit 1
fi

export PYTHONUNBUFFERED=1
ALEMBIC=(alembic -c /code/alembic.ini)

echo "fly_release_migrate: checking current revision (120s max)…"
if timeout 120 "${ALEMBIC[@]}" current; then
  echo "fly_release_migrate: current revision logged above"
else
  echo "fly_release_migrate: WARN — alembic current failed or timed out; continuing to upgrade head" >&2
fi

echo "fly_release_migrate: upgrade head (900s max)…"
timeout 900 "${ALEMBIC[@]}" upgrade head

echo "fly_release_migrate: done $(date -u +%Y-%m-%dT%H:%M:%SZ)"
