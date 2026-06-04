#!/usr/bin/env bash
# Push ADMIN_KEY from .env to Fly (safe quoting — no commas/spaces in value required).
#
# Usage:
#   ./scripts/sync_fly_admin_key.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo "No .env file — create ADMIN_KEY=... first" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

if [[ -z "${ADMIN_KEY:-}" ]]; then
  echo "ADMIN_KEY is empty in .env" >&2
  exit 1
fi

if [[ "$ADMIN_KEY" == *" "* ]] || [[ "$ADMIN_KEY" == *","* ]]; then
  echo "ADMIN_KEY must not contain spaces or commas (Fly CLI parses those as separate secrets)." >&2
  exit 1
fi

echo "Setting Fly secret ADMIN_KEY from .env (length ${#ADMIN_KEY})..."
fly secrets set "ADMIN_KEY=${ADMIN_KEY}" -a ready-2-robot
echo "Done. Wait ~60s for machines to restart, then: ./scripts/run_lead_enrich_agent.sh"
