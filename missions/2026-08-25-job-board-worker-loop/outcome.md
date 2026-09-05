# Outcome — Job-board scraper on Fly worker

**Mission:** `missions/2026-08-25-job-board-worker-loop`  
**Date:** 2026-08-25

## What shipped

- Fly worker starts a dedicated `job-board-scraper` thread beside intelligence news (`SKIP_CELERY=1`).
- Industry URL lookup is case-insensitive (`hospitality` matches `Hospitality`).
- Manual `/api/scraper/run/job_boards` and `/run-all` run job boards in-process when Celery is skipped.
- Rejected company names skip the posting; `robot_jobs` persist is committed.
- `/api/pipeline-stats` and `/api/scraper-health` expose `robot_jobs` counts.

Intelligence news, Jobs UI, and SIGNAL CRM are unchanged. Kill switch: `ENABLE_SCHEDULED_JOB_BOARD=0`.

## Tests

`PYTHONPATH=/workspace pytest tests/test_job_board_scraper_pipeline.py tests/test_robot_job_extract.py tests/test_scraper_food_automation_queries.py` — 17 passed.

## Deploy (Fly `ready-2-robot`)

- Image `deployment-01M0WT1CQ2JVVVPPET3ET1KQG1`. Web + worker started.
- Worker boot: intelligence thread still starts; **job-board thread started** (`every 6 hours, first run in 12 min`).
- Jobs match API unchanged: Locus URL → `state=matches`, `job_count=26`.
- `/api/pipeline-stats` now includes `robot_jobs` (still 0 until Indeed HTML yields postings — datacenter IPs often get a challenge page).
- One-shot worker run `industry=Hospitality` with 1 URL returned `{status: ok, urls: 1}` without crashing the worker.

## Follow-ups

- Watch `robot_jobs.last_24h` after the 12-minute first cycle. If still 0, Indeed anti-bot is the next yield problem (pipeline is no longer idle).
- Hotel / RSS / SERP remain Celery-only on Fly (out of scope).
