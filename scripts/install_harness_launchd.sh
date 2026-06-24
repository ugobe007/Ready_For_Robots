#!/usr/bin/env bash
# Install a macOS launchd job that runs the harness loop daily at 7:00 local time.
#
# Usage:
#   ./scripts/install_harness_launchd.sh
#   ./scripts/install_harness_launchd.sh --uninstall
#
# Requires repo-root .env with ANTHROPIC_API_KEY, DATABASE_URL, ADMIN_KEY.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LABEL="com.readyforrobots.harness-daily"
PLIST="$HOME/Library/LaunchAgents/${LABEL}.plist"
VENV="${ROOT}/.venv-harness"
LOG_DIR="${ROOT}/reports"
UNINSTALL=false

for arg in "$@"; do
  case "$arg" in
    --uninstall) UNINSTALL=true ;;
  esac
done

if [ "$UNINSTALL" = true ]; then
  launchctl bootout "gui/$(id -u)/${LABEL}" 2>/dev/null || true
  rm -f "$PLIST"
  echo "Removed ${PLIST}"
  exit 0
fi

if [ ! -d "$VENV" ]; then
  echo "Creating ${VENV}…"
  python3 -m venv "$VENV"
fi

# shellcheck disable=SC1091
source "${VENV}/bin/activate"
pip install -q -r "${ROOT}/requirements-harness.txt" \
  -r "${ROOT}/harness/requirements.txt" \
  -r "${ROOT}/requirements.txt"

mkdir -p "$LOG_DIR"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${LABEL}</string>
  <key>WorkingDirectory</key>
  <string>${ROOT}</string>
  <key>ProgramArguments</key>
  <array>
    <string>${VENV}/bin/python3</string>
    <string>${ROOT}/scripts/harness_daily.py</string>
  </array>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
  </dict>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key>
    <integer>7</integer>
    <key>Minute</key>
    <integer>0</integer>
  </dict>
  <key>StandardOutPath</key>
  <string>${LOG_DIR}/harness_daily_stdout.log</string>
  <key>StandardErrorPath</key>
  <string>${LOG_DIR}/harness_daily_stderr.log</string>
</dict>
</plist>
EOF

launchctl bootout "gui/$(id -u)/${LABEL}" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
launchctl enable "gui/$(id -u)/${LABEL}"
echo "Installed daily harness at 7:00 local time."
echo "Logs: ${LOG_DIR}/harness_daily_*.log"
echo "Test now: ${VENV}/bin/python3 ${ROOT}/scripts/harness_daily.py --dry-run"
