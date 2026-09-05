#!/usr/bin/env bash
# Rebuild pipeline/homepage public caches.
#
# Local (writes to DATABASE_URL in .env / .env.local):
#   ./scripts/run_refresh_pipeline_cache.sh
#
# Remote Fly admin (needs ADMIN_KEY in .env + deployed endpoint):
#   ./scripts/run_refresh_pipeline_cache.sh --remote
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ "${1:-}" == "--remote" ]]; then
  exec python3 scripts/refresh_pipeline_cache.py --remote "${@:2}"
fi

exec python3 scripts/refresh_pipeline_cache.py "$@"
