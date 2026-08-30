# Robot Job scrapers

**Status:** extract + close-out classifiers live; job board persist onto `robot_jobs`  
**Production:** Fly worker in-app thread (`SKIP_CELERY=1`). Celery Beat is local/Redis only.  
**Does not:** invent wages, invent jobs, treat VP Ops hires as Robot Jobs

Job board scrapers used to score **buyer personas**. They now extract **Robot Jobs** from operational postings.

## Extract (`app/services/robot_job_extract.py`)

From title + description, only if stated:

| Field | Example |
|-------|---------|
| Job title / function | Order Picker → `picking` |
| Compensation | `$18–$22 an hour`, signing bonus |
| Performance specs | `45 cases per hour`, `50 lbs`, night shift, openings |
| Employer email | `mailto:`, JSON-LD `email`, `hiringOrganization.email` — page only |

Unknown is stored on `unknowns`. Never fill with a guess. Never invent `info@` from the employer name. Skip board mailboxes (`jobs@indeed.com`, `noreply@indeed.com`).

Signal text: `ROBOT_JOB | {title} | {function} | {pay} | {specs} | {status} | {employer}`  
`signal_type`: `robot_job` (not HOT buyer intent).

## Contacts (page only)

`extract_job_contacts` reads **this posting**: `mailto:` hrefs, schema.org `itemprop=email`, JSON-LD `JobPosting.email` / `hiringOrganization.email` / `applicationContact.email`. It does **not** scrape LinkedIn, Apollo, Hunter, or SIGNAL buyer lists.

`upsert_robot_job_from_extract` writes `employer_email`, `contact_url`, `apply_url` onto `robot_jobs` (Alembic `jcnt0a1b2c3d4`) and mirrors them in `requirements` JSONB so FIND overlay still works if Fly has not migrated yet. FIND Job Cards copy those fields; apply send (`can_operator_send`) turns on when a real mailbox is present.

**Fly leftover:** `alembic upgrade head` (revision `jcnt0a1b2c3d4`). Until Fly runs it, column writes are skipped and contacts live only in `requirements`.

**Backfill:** posting HTML is **not** stored (`job_evidence.excerpt` is the signal line). `scripts/backfill_robot_job_contacts.py` cannot recover the existing ~1,664 empty mailboxes. New scrapes fill going forward.

## Close-out (`app/services/robot_job_lifecycle.py`)

Re-read public text against an existing job:

| Status | When |
|--------|------|
| `open` | Posting still describes human work |
| `filled_by_robot` | Employer + work family + robot now performing it |
| `withdrawn` | Board says expired / not accepting |
| `incumbent_robot` | Employer has a robot; task match is weak |

This is employment close-out, not CRM closed-won.

News queries in `scrape_targets.NEWS_QUERIES` hunt deployment evidence so the same classifier can close watched jobs.

## Persist

`upsert_robot_job_from_extract` writes `robot_jobs.requirements` JSONB (`compensation`, `performance_specs`, `job_function`, contacts when found) and attaches `job_evidence`. Contact columns: Alembic `jcnt0a1b2c3d4` — **Fly leftover until `alembic upgrade head`**.

## Production schedule

`app/services/job_board_scraper_runner.py` is the shared runner (Celery task + Fly thread + admin trigger).

| Env | Default | Role |
|-----|---------|------|
| `ENABLE_SCHEDULED_JOB_BOARD` | `1` | Worker thread on/off. Does not affect intelligence news. |
| `JOB_BOARD_EVERY_HOURS` | `6` | Interval between full industry rotations |
| `JOB_BOARD_FIRST_RUN_DELAY_MINUTES` | `12` | Stagger after boot so news can start first (5 min) |
| `JOB_SCRAPER_MAX_URLS_PER_RUN` | `18` | Cap per industry |

Industry URL lookup is case-insensitive (`hospitality` == `Hospitality`). Yield: `GET /api/pipeline-stats` → `robot_jobs`.

Relevancy scoring includes operational titles (`LABOR_PAIN_KEYWORDS` plus title stems: Cook, Server, Warehouse Worker, EVS). Robot-builder roles (`robotics engineer`, …) still score 0. Operational URLs are scraped before buyer-persona URLs. Page logs: `page yield found= robot_jobs= skipped_relevancy=`. JSON-LD `JobPosting` is a fallback when CSS cards are missing.
