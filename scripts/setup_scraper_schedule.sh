#!/bin/bash
# Set up automated schedule for intelligence scraper (no Redis/Celery needed)
# Run once to enable cron or launchd scheduling

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CRON_SCRIPT="$PROJECT_ROOT/scripts/run_intelligence_scraper_cron.sh"
PLIST_DEST="$HOME/Library/LaunchAgents/com.readyforrobots.scraper.plist"

echo "=============================================="
echo "  Scraper Schedule Setup"
echo "  Project: $PROJECT_ROOT"
echo "=============================================="
echo ""

# Make cron script executable
chmod +x "$CRON_SCRIPT"
echo "✓ Cron script is executable"
echo ""

# Ensure logs dir exists
mkdir -p "$PROJECT_ROOT/logs"

echo "Choose scheduling method:"
echo "  1) launchd (recommended on macOS – runs when machine wakes)"
echo "  2) cron (simple, runs at 9am, 3pm, 9pm)"
echo ""
read -p "Enter 1 or 2 [default: 1]: " choice
choice=${choice:-1}

if [ "$choice" = "1" ]; then
    echo ""
    echo "Installing launchd schedule..."
    cat > "$PLIST_DEST" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.readyforrobots.scraper</string>
    <key>ProgramArguments</key>
    <array>
        <string>$CRON_SCRIPT</string>
    </array>
    <key>StartCalendarInterval</key>
    <array>
        <dict><key>Hour</key><integer>9</integer><key>Minute</key><integer>0</integer></dict>
        <dict><key>Hour</key><integer>15</integer><key>Minute</key><integer>0</integer></dict>
        <dict><key>Hour</key><integer>21</integer><key>Minute</key><integer>0</integer></dict>
    </array>
    <key>StandardOutPath</key>
    <string>$PROJECT_ROOT/logs/launchd_scraper.log</string>
    <key>StandardErrorPath</key>
    <string>$PROJECT_ROOT/logs/launchd_scraper_err.log</string>
    <key>WorkingDirectory</key>
    <string>$PROJECT_ROOT</string>
</dict>
</plist>
EOF
    launchctl load "$PLIST_DEST" 2>/dev/null || launchctl load -w "$PLIST_DEST"
    echo "✓ launchd schedule installed"
    echo ""
    echo "Runs at 9am, 3pm, 9pm local time."
    echo "Logs: $PROJECT_ROOT/logs/launchd_scraper*.log"
    echo ""
    echo "To stop:  launchctl unload $PLIST_DEST"
    echo "To check: launchctl list | grep readyforrobots"
elif [ "$choice" = "2" ]; then
    echo ""
    echo "Add this line to your crontab (crontab -e):"
    echo ""
    echo "  # Intelligence scraper: 9am, 3pm, 9pm"
    echo "  0 9,15,21 * * * $CRON_SCRIPT"
    echo ""
    echo "Ensure .env exists with DATABASE_URL set."
    echo "Logs: $PROJECT_ROOT/logs/intelligence_scraper_YYYYMMDD.log"
else
    echo "Invalid choice."
    exit 1
fi

echo ""
echo "=============================================="
echo "  Done"
echo "=============================================="
