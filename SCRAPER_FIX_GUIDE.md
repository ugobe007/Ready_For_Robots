# Scraper Fix Guide — Reliable Lead Generation

If scrapers aren't producing leads, follow these steps.

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

**Want more new leads?** Run the full query set (no `--max-queries`). The first 20 queries skew toward warehouse/logistics — if your DB already has many of those, you'll get more "enriched" than "new". Full run hits 70+ diverse industries (medical, airport, retail, food, etc.) for better discovery:
```bash
.venv_new/bin/python scripts/run_intelligence_scraper.py --mode discover --limit 15
```

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
| **Local cron** | Highest | Add crontab, set DATABASE_URL in .env |
| **cron-job.org** | High | Create job, set SCRAPER_CRON_TOKEN |
| **Fly + Celery** | Medium | Need REDIS_URL (Upstash) |
| **Manual run-all** | Medium | POST /api/scraper/run-all — in-process quick scrape runs even without Celery |

**Recommended**: Set up **local cron** (step 2) for reliable daily leads. Use **run-all** or **cron-job.org** as backup.
