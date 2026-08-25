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

## Follow-ups

- After deploy: worker log `In-app scheduled job-board thread started`; first cycle ~12 min later.
- Watch `GET /api/pipeline-stats` → `robot_jobs.last_24h` (Indeed may still block datacenter IPs).
- Hotel / RSS / SERP still Celery-only on Fly (out of scope).
