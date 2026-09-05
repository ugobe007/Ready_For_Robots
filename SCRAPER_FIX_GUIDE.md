# Scraper Fix Guide — Reliable Lead Generation

If scrapers aren't producing leads, follow these steps.

---

## 0. In-App Scheduler (Fly.io — No Setup Required)

**On Fly.io** the web app now runs the intelligence scraper automatically:

- When `FLY_APP_NAME` is set (default on Fly), a background thread starts on app startup.
- **First run:** 5 minutes after deploy (configurable: `SCRAPER_FIRST_RUN_DELAY_MINUTES`).
- **Then every 6 hours** (configurable: `RUN_SCRAPER_EVERY_HOURS=6`).
- Each run is a quick pass: 20 queries, ~3–5 min, plus enrichment.
- No Redis or Celery required. To disable: `ENABLE_SCHEDULED_SCRAPER=0` or set `RUN_SCRAPER_EVERY_HOURS=0`.

So after deploy, leads should start flowing within ~10–15 minutes and then every 6 hours. Check `/api/scraper/stats/daily?days=1` and `/api/leads/summary` to confirm.

**Static Next.js frontend (`output: 'export'`):** the UI has no server-side `/api` routes. All browser calls use `getApiBase()` from `frontend/nextjs/lib/apiBase.js`. Set **`NEXT_PUBLIC_API_URL`** at build time to your FastAPI origin (e.g. `https://readyforrobots.com` or your Fly app URL) so the homepage, admin scraper controls, and analytics hit the live API. Local dev without that var uses `http://localhost:8000` when `NODE_ENV=development` or the hostname is localhost.

---

## 1. Run a Quick Test (In-Process, No Celery)

**From your Mac** — the script auto-loads `DATABASE_URL` from `.env`:

```bash
cd ~/Desktop/Ready_For_Robots

# Ensure .env has DATABASE_URL (Supabase → Settings → Database → Connection string)
# Format: postgresql://postgres:PASSWORD@db.PROJECT_REF.supabase.co:5432/postgres
# Do NOT use db.xxx.supabase.co — use your actual host (e.g. db.xxxxx.supabase.co)

# Quick test (20 queries, ~3 min) — queries are shuffled so you hit diverse industries
.venv_new/bin/python scripts/run_intelligence_scraper.py --mode discover --limit 10 --max-queries 20

# Full run (all queries, 30+ min)
.venv_new/bin/python scripts/run_intelligence_scraper.py --mode both --limit 35
```

If this works, you'll see "New Companies Found" and "Signals Created". Your DB connection and scraper logic are fine.

**Want more new leads?** Run the full query set (no `--max-queries`). The first 20 queries skew toward warehouse/logistics — if your DB already has many of those, you'll get more "enriched" than "new". Full run hits 200+ diverse industries (medical, airport, retail, food, etc.) for better discovery:
```bash
.venv_new/bin/python scripts/run_intelligence_scraper.py --mode discover --limit 15
```

If you still see low "New Companies Found" (e.g. only 2): the scraper extracts company names from article text; most articles may match companies you already have (counted as "Enriched"). Running with **no --max-queries** and a higher **--limit** (e.g. 20–25) processes more articles across more industries and increases the chance of discovering companies not yet in your DB.

---

## 2. Schedule Locally (Most Reliable)

Run the scraper from your Mac on a schedule. No Fly, no Celery, no Redis.

**Setup cron** (runs 3x daily at 9am, 3pm, 9pm):

```bash
crontab -e
```

Add:

```
0 9,15,21 * * * cd /Users/leguplabs/Desktop/Ready_For_Robots && .venv_new/bin/python scripts/run_intelligence_scraper.py --mode both --limit 35 >> logs/scraper.log 2>&1
```

**Or use the project's cron script**:

```bash
chmod +x scripts/run_intelligence_scraper_cron.sh
# Add to crontab:
# 0 9,15,21 * * * /Users/leguplabs/Desktop/Ready_For_Robots/scripts/run_intelligence_scraper_cron.sh
```

Make sure `.env` has `DATABASE_URL` pointing to Supabase.

---

## 3. Use External Cron (cron-job.org)

1. Go to [cron-job.org](https://cron-job.org) (free)
2. Create a job:
   - **URL**: `https://readyforrobots.com/api/scraper/cron/run-intelligence?token=YOUR_SECRET`
   - **Schedule**: Daily at 9am (or 3x daily)
   - **Method**: GET

3. **Set the secret on Fly**:
   ```bash
   fly secrets set SCRAPER_CRON_TOKEN=your-random-secret-here
   ```
   Use the same value in the cron URL.

This wakes your Fly app and triggers a quick scrape (20 queries, ~3 min).

---

## 4. Fix Celery/Redis (If You Want Full Automation)

Celery tasks (job boards, news, RSS, etc.) need Redis. If `tasks` shows `"celery": "unavailable"` when you run `/api/scraper/run-all`, Redis isn't configured.

**Check Fly secrets**:

```bash
fly secrets list -a ready-2-robot
```

You need:
- `DATABASE_URL` — Supabase connection string
- `REDIS_URL` — e.g. Upstash: `rediss://default:xxx@xxx.upstash.io:6379`

**Add Redis (Upstash, free tier)**:
1. [Upstash](https://upstash.com) → Create Redis
2. Copy the Redis URL
3. `fly secrets set REDIS_URL="rediss://default:xxx@xxx.upstash.io:6379"`

**Verify Celery in logs**:
```bash
fly logs -a ready-2-robot
```
Look for "celery@... ready" or Redis connection errors.

---

## 5. Daily Opportunity Analytics Report

**What automation is inferred? What robots are needed? ROI expectations? Common tasks?**

```bash
# Run locally
.venv_new/bin/python scripts/run_daily_analytics_report.py --days 7 --save

# Or via API (JSON or markdown)
curl "https://readyforrobots.com/api/daily-report?days=7&format=markdown"
```

Scheduled daily at 9:15am UTC. Report saved to `reports/daily_analytics_latest.md`.

---

## 6. Verify Leads After a Run

```bash
curl "https://readyforrobots.com/api/scraper/stats/daily?days=1"
```

Check `companies_last_24h` and `signals_last_24h`. If they're still 0 after a run, the scraper may be failing silently or the DB connection may be wrong.

---

## 7. Summary: What to Do Now

| Option | Reliability | Setup |
|--------|-------------|-------|
| **Fly in-app scheduler** | High | Automatic on Fly (every 6h); no setup |
| **Local cron** | Highest | Add crontab, set DATABASE_URL in .env |
| **cron-job.org** | High | Create job, set SCRAPER_CRON_TOKEN |
| **Fly + Celery** | Medium | Need REDIS_URL (Upstash) |
| **Manual run-all** | Medium | POST /api/scraper/run-all — in-process quick scrape runs even without Celery |

**Recommended**: On Fly, the **in-app scheduler** (step 0) runs automatically. For more leads, add **local cron** (step 2) or **cron-job.org** as backup.

---

## 8. Playwright (hotel / job-board / Yellow Pages scrapers)

RSS-based scrapers (intelligence news, news, SERP) only need Python + `DATABASE_URL`. **Browser-based** scrapers also need a **downloaded Chromium** via Playwright:

- `HotelDirectoryScraper` (Yellow Pages)
- `JobBoardScraper` (and enhanced variants)
- Anything in the orchestrator that launches Chromium

**One-time setup** (use the same venv as the guide, e.g. `.venv_new`):

```bash
cd ~/Desktop/Ready_For_Robots
.venv_new/bin/pip install playwright   # if not already in requirements
.venv_new/bin/playwright install chromium
```

If you see `Executable doesn't exist at ... ms-playwright/chromium...`, run `playwright install chromium` again after any Playwright package upgrade. `scraper_health.json` will show browser launch failures until this is done.

---

## 9. Deploy & startup (no DB at deploy)

The app **does not connect to the database at deploy or at process start**. The DB is used only when a request needs it (e.g. first time someone loads a page that calls `/api/leads/summary` or any API that uses the DB).

- **Startup**: No `create_all()` or DB connection in `app.main` or `worker.tasks`. Health check (`/health`) returns immediately without touching the DB.
- **Migrations**: Run in the background in `scripts/start_all.sh` so uvicorn starts right away. If migrations fail, run `alembic upgrade head` manually (e.g. `fly ssh console -a ready-2-robot` then `alembic upgrade head`).
- **Streamline**: `fly deploy` → build → start container → uvicorn listens on 8080; first browser/API request that needs data will open the DB connection.
