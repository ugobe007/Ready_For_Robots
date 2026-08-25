# Job-board scraper actually runs on Fly

**Date:** 2026-08-25  
**Type:** build  
**Agent:** PipelineHealth + Deploy  
**Status:** in progress

## Goal

Robot Job board ingest was wired in code and Celery Beat but **never ran on Fly** (`SKIP_CELERY=1`, in-app loop was news-only). `robot_jobs` stayed empty. Restore the FIND supply path: job boards → `robot_job` signals → `robot_jobs`, without stopping the intelligence news loop or the Jobs terminal workflow.

## Acceptance

- Fly worker starts a **separate** `job-board-scraper` thread; intelligence thread still starts
- `ENABLE_SCHEDULED_JOB_BOARD=0` kills job boards only
- Web process does not start job-board scraping
- `get_urls("job_board", industry="hospitality")` returns the Hospitality boards (case-insensitive)
- Manual `POST /api/scraper/run/job_boards` runs in-process when `SKIP_CELERY=1`
- Rejected company names skip the posting; they do not abort the page
- `/api/pipeline-stats` exposes `robot_jobs` counts (additive)

## Out of scope

- Hotel / RSS / SERP / RFP in-app threads
- Matcher ranking, Jobs UI, SIGNAL CRM
