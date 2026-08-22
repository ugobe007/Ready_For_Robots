# Outcome — CRM jobs watch

**Mission:** `missions/2026-08-22-crm-jobs-watch`  
**Type:** build

## Shipped

- `/crm` uses Jobs chrome: Kare face, emerald **CRM** headline, numbered how-to, opt-in for job-change / new-work email.
- `PUT /api/crm/jobs-watch` records the robot URL on `robot_submissions` (source `jobs_watch`) and `jobs_watches`.
- Daily Celery beat `jobs-watch-daily` (12:00 UTC) re-runs `compose_robot_job_search`, diffs `job_key`s, emails new work via Resend. First cron pass seeds the snapshot without emailing the whole list.
- Free taste: 1 robot, 2 alerts, 3 unlocked CRM events. Extra events show as locked Pro teases. Paid: unlimited robots/alerts.

## Verify

- `python3 -m pytest tests/test_jobs_watch.py tests/test_plan_entitlements.py -q` — 24 passed
- `npx vitest run client/src/lib/jobsWorkflow.test.ts` — 23 passed
- Local `/crm` (Vite :3003): Kare face, emerald CRM headline, how-to, opt-in checkbox. Auth is not configured, so opt-in stays disabled with sign-in copy.

## Follow-ups

- Deploy includes Alembic `jwch0a1b2c3d4` — do not `--skip-release-command`.
- Worker must pick up `run_jobs_watch_task` on the next Fly deploy.
