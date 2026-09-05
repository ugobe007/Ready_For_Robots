#!/usr/bin/env bash
# Commit (optional), push to origin, deploy backend to Fly.io.
# Frontend (readyforrobots.com) deploys via Vercel on push to main.
#
# Usage:
#   ./scripts/ship.sh "Fix Cal outreach email inference"
#   ./scripts/ship.sh                    # commit with default message if there are changes
#   SKIP_COMMIT=1 ./scripts/ship.sh      # push + deploy only (already committed)
#   SKIP_DEPLOY=1 ./scripts/ship.sh "…"  # commit + push only
#
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

APP="${FLY_APP:-ready-2-robot}"
BRANCH="${SHIP_BRANCH:-main}"
DEFAULT_MSG="Ship Ready For Robots updates."

die() { echo "error: $*" >&2; exit 1; }

command -v git >/dev/null || die "git not found"
command -v fly >/dev/null || command -v flyctl >/dev/null || die "fly/flyctl not found"

FLY="${FLY_CMD:-$(command -v fly || command -v flyctl)}"

if [[ "${SKIP_COMMIT:-0}" != "1" ]]; then
  if git diff --quiet && git diff --cached --quiet && [[ -z "$(git status --porcelain)" ]]; then
    echo "No local changes to commit."
  else
    MSG="${1:-$DEFAULT_MSG}"
    # Never stage secrets
    if git status --porcelain | grep -qE '^.. \.env$|^.. \.env\.'; then
      echo "warning: .env has changes — not staging (gitignored)."
    fi
    git add -A
    if git diff --cached --quiet; then
      echo "Nothing staged after git add (check .gitignore)."
    else
      git commit -m "$MSG"
      echo "Committed: $MSG"
    fi
  fi
fi

echo "Pushing to origin/$BRANCH …"
git push -u origin "HEAD:$BRANCH"

if [[ "${SKIP_DEPLOY:-0}" == "1" ]]; then
  echo "SKIP_DEPLOY=1 — skipping Fly deploy."
  exit 0
fi

echo "Deploying $APP to Fly.io (immediate strategy) …"
# Applies staged Fly secrets and rolls the app in one step.
"$FLY" deploy -a "$APP" --strategy immediate

echo ""
echo "Done."
echo "  Backend: https://ready-2-robot.fly.dev/"
echo "  Frontend: Vercel auto-deploy from push to $BRANCH (readyforrobots.com)"
echo ""
echo "If you only updated Fly secrets, redeploy is enough:"
echo "  fly secrets set KEY=value -a $APP && $FLY deploy -a $APP --strategy immediate"
