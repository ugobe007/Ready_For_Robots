#!/usr/bin/env bash
# Run sales-lead enrichment agent on production (top N pipeline companies).
#
# Auth (first match wins):
#   - X-Admin-Key from ADMIN_KEY in .env or environment
#   - ?token= from SCRAPER_CRON_TOKEN in .env or environment
#
# Usage:
#   ./scripts/run_lead_enrich_agent.sh
#   ./scripts/run_lead_enrich_agent.sh 50
#   API_BASE=https://ready-2-robot.fly.dev ./scripts/run_lead_enrich_agent.sh 300
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

LIMIT="${1:-300}"
API_BASE="${API_BASE:-https://ready-2-robot.fly.dev}"
URL="${API_BASE}/api/admin/leads/enrich-agent?limit=${LIMIT}"

if [[ -n "${ADMIN_KEY:-}" ]]; then
  echo "→ POST ${URL} (X-Admin-Key)"
  curl -sS -X POST "$URL" -H "X-Admin-Key: ${ADMIN_KEY}"
elif [[ -n "${SCRAPER_CRON_TOKEN:-}" ]]; then
  echo "→ POST ${URL}&token=*** (SCRAPER_CRON_TOKEN)"
  curl -sS -X POST "${URL}&token=${SCRAPER_CRON_TOKEN}"
else
  echo "Missing ADMIN_KEY or SCRAPER_CRON_TOKEN in environment or .env" >&2
  echo "Set one with: fly secrets set ADMIN_KEY='your-secret' -a ready-2-robot" >&2
  exit 1
fi
echo ""
