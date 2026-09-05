# Scraper Diagnostic Report

## Summary

Several issues prevent the scrapers from running correctly. The main blockers are:

1. **Broken virtual environment** – `.venv` was created on another machine (path points to `/Users/robertchristopher/...`) and no longer works
2. **Dependencies not installed** – System `python3` lacks SQLAlchemy and other project dependencies
3. **`run_scrapers_supabase.sh` uses raw `python3`** – It never activates a venv or uses a project-specific Python

## Scraper Architecture

| Scraper | Script | Data Source | Dependencies |
|---------|--------|-------------|--------------|
| **Intelligence News** | `scripts/run_intelligence_scraper.py` | Google News RSS | urllib, SQLAlchemy, inference engine |
| **News** | `app/scrapers/news_scraper.py` | Google News RSS | urllib, SQLAlchemy |
| **SERP** | `app/scrapers/serp_scraper.py` | Google News RSS | urllib, SQLAlchemy |
| **Job Board** | `app/scrapers/job_board_scraper.py` | Job site HTML | **Playwright**, BeautifulSoup |
| **Orchestrator** | `app/scrapers/orchestrator.py` | All of the above | Full stack |

## Last Known Good Run

`intelligence_scraper.log` shows the intelligence scraper completed on **March 6, 2026** with:
- 120 articles processed
- 43 queries run
- 32 companies discovered
- 32 signals created

So the scraper logic works when the environment is correctly set up.

## Fix Steps

### 1. Recreate the virtual environment

```bash
cd /Users/leguplabs/Desktop/Ready_For_Robots

# Remove broken venv (optional - backup first)
# mv .venv .venv.broken

# Create fresh venv (SCRAPER_FIX_GUIDE uses .venv_new; run_scrapers_supabase.sh prefers it)
python3 -m venv .venv_new

# Activate and install dependencies
source .venv_new/bin/activate   # On macOS/Linux
pip install -r requirements.txt

# Playwright browsers (required for JobBoardScraper, HotelDirectoryScraper)
playwright install chromium
```

### 2. Use the run script with the venv

`run_scrapers_supabase.sh` has been updated to use a project Python. Ensure `.env` has `DATABASE_URL` set for Supabase.

```bash
./scripts/run_scrapers_supabase.sh
```

### 3. Manual test (intelligence scraper only)

```bash
source .venv_new/bin/activate
python scripts/run_intelligence_scraper.py --limit 2 --max-queries 5
```

### 4. Full pipeline (orchestrator)

```bash
source .venv_new/bin/activate
python app/scrapers/orchestrator.py
```

Note: The orchestrator uses JobBoardScraper, which needs Playwright and real job board URLs. Job boards may block automated scraping.

## Quality Notes (from logs)

The intelligence scraper’s entity extraction sometimes creates false positives, e.g.:
- "in funding - The Robot"
- "Criticize State Leaders - U.S. News & World"
- "Chicken restaurant chain"

These come from regex matching; consider tightening `_is_valid_company_name()` in `intelligence_news_scraper.py`.

## Database

Scrapers expect `DATABASE_URL` in `.env` (Supabase Postgres or local SQLite). The app supports:
- `postgres://` / `postgresql://` (converted to `postgresql+psycopg2://`)
- `sqlite:///./ready_for_robots.db` for local dev
