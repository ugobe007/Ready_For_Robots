# Scraper Automation Schedule

## Quick Start (recommended)

Run once to set up automated scraping (9am, 3pm, 9pm local time):

```bash
./scripts/setup_scraper_schedule.sh
```

Choose **launchd** (macOS) or **cron**. No Redis or Celery required. Uses the direct `run_intelligence_scraper.py` script.

---

## Manual options

The intelligence scraper (and other scrapers) can run on an automated schedule. Two options:

---

## Option 1: Cron (Simplest – No Redis)

Use system cron to run the intelligence scraper 3× daily.

### Setup

1. Make the script executable:
   ```bash
   chmod +x scripts/run_intelligence_scraper_cron.sh
   ```

2. Add to crontab (`crontab -e`):
   ```
   # Intelligence scraper: 9am, 3pm, 9pm (local time)
   0 9,15,21 * * * /Users/leguplabs/Desktop/Ready_For_Robots/scripts/run_intelligence_scraper_cron.sh
   ```

3. Ensure `DATABASE_URL` is set in `.env` (or your shell when cron runs).

### macOS: Run when not logged in (launchd)

Cron may not run when the Mac is asleep. Use launchd for reliable scheduling:

1. Copy and edit the plist (fix the path if needed):
   ```bash
   cp scripts/com.readyforrobots.scraper.plist.example ~/Library/LaunchAgents/com.readyforrobots.scraper.plist
   # Edit the paths in the plist to match your project location
   ```

2. Load it:
   ```bash
   launchctl load ~/Library/LaunchAgents/com.readyforrobots.scraper.plist
   ```

3. Unload to stop:
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.readyforrobots.scraper.plist
   ```

---

## Option 2: Celery + Redis (Full Schedule)

Runs all scrapers (intelligence, news, job boards, SERP, etc.) on their full schedule.

### Prerequisites: Redis

**Option A – Homebrew (macOS):**
```bash
brew install redis
brew services start redis
```

**Option B – Docker:**
```bash
docker compose -f docker-compose.redis.yml up -d
```
Ensure `.env` has `REDIS_URL=redis://localhost:6379/0` (or leave unset – that’s the default).

### Run

```bash
./scripts/start_scraper_scheduler.sh       # Normal start
./scripts/start_scraper_scheduler.sh --dev # Dev: reset schedule, fire overdue tasks now
```

This starts:
- **Celery worker** – executes scraper tasks
- **Celery beat** – sends tasks on schedule

**If it looks "stuck"**: A heartbeat task runs every 2 min—you should see `[HEARTBEAT] Scheduler alive` in the logs. Scrapers run at their scheduled times (e.g. news at 6am/8am/10am UTC). Use `--dev` to reset the schedule so overdue tasks run immediately on start.

### Schedule (UTC)

| Scraper | Frequency |
|---------|-----------|
| **Intelligence (lead discovery)** | 9am, 3pm, 9pm |
| News (general) | Every 2h (6am–4pm) |
| Manufacturing news | 7:30am, 3:30pm |
| Job boards | Every 6h |
| RSS feeds | Every 4h |
| SERP expansion | 12am, 8am, 4pm |
| Hotel directory | Daily 3am |
| Logistics directory | Daily 4am |
| RFP marketplace | Daily 5am |
| Rescore companies | Daily 6am |
| Scheduler heartbeat | Every 2 min (proves pipeline is alive) |
| Health check | Hourly |

### Run in background

```bash
nohup ./scripts/start_scraper_scheduler.sh > logs/celery_scheduler.log 2>&1 &
```

---

## Option 3: PM2 (Node.js)

If you use PM2, add the intelligence scraper to `ecosystem.config.js` and use `cron_restart` for scheduling.

---

## Run scrapers directly (no Celery)

To verify scrapers work without the scheduling layer:

```bash
# Intelligence scraper (discover new leads)
python scripts/run_intelligence_scraper.py --mode discover --limit 5

# Or use Celery to trigger a task on demand:
python -m celery -A worker.celery_worker call worker.tasks.run_intelligence_scraper_task
```

## Verify

- **Cron**: Check `logs/intelligence_scraper_YYYYMMDD.log`
- **Celery**: You should see `[HEARTBEAT] Scheduler alive` every 2 min. Check worker output or `logs/celery_scheduler.log`
- **Database**: `SELECT COUNT(*), source FROM companies GROUP BY source;`
