# Outcome: One CTA on Jobs, 5 example jobs, digest owned in-repo

**Date:** 2026-08-20
**Mission:** `missions/2026-08-20-jobs-one-cta-five-cap`

## Diff

- Jobs terminal always caps example jobs at 5 (`capExampleJobs`). Copy says 5 shown.
- Jobs step: one buyer-leads CTA. Sidebar All/New robot are quiet text. No “See all matches” signup box. Job cards are evidence only.
- Portfolio: one CTA (see jobs). Buyer leads stay on the Jobs step.
- Results from Jobs: 5 leads, Jobs chrome, no signup wall before those 5. Never inflate to 15 on `/results`.
- Pipeline from Jobs: skip SIGNAL hero; Jobs-continuity header. >5 lives here.
- Daily digest: Fly web backup when `SKIP_CELERY=1` + Celery Beat + GitHub Action `cal-daily-digest.yml`. Hermes skill retired (no AI Gateway cron).

## Tests

```
npx vitest run client/src/lib/jobsWorkflow.test.ts   # 7 passed
npx tsc --noEmit                                     # passed
/tmp/rfr-venv/bin/python -m pytest tests/test_cal_daily_digest.py tests/test_hermes_intelligence_ingest.py tests/test_paid_llm_gate.py
# 18 passed; 2 pre-existing sqlite ingest dry-run failures (companies table)
```

## Follow-ups

- Confirm GitHub Actions secret `ADMIN_KEY` is set so the 15:05 UTC backup can POST (Fly in-process still sends if the secret is missing).
