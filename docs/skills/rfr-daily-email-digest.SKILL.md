---
name: rfr-daily-email-digest
description: "RETIRED. Fly + GitHub Actions send the digest. Do not cron this on Hermes."
version: 0.3.0
author: Ready For Robots
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Robotics, Email, Digest, ReadyForRobots, Retired]
    related_skills: [rfr-sales-floor-manager, rfr-qualify-match]
---

# ReadyForRobots daily email digest — RETIRED ON HERMES

**Hermes is retired (2026-08-26).** Do not schedule this skill. FIND is `/`. See [`hermes_retired.md`](../hermes_retired.md).

**Do not schedule this skill on Hermes.** The previous Hermes cron used `--provider ai-gateway` and failed HTTP 402 before any `curl` ran. That cron is retired.

## Who sends the digest now (Hermes is not in this path)

Fly and GitHub Actions own this email. A leftover Hermes job with `--provider ai-gateway` can 402; that failure does **not** block the digest. Do not add a Hermes cron for this skill.

1. Fly in-process scheduler (`ENABLE_SCHEDULED_CAL_DAILY_DIGEST=1`, 15:00 UTC) on the **worker only**
2. Celery Beat `cal-daily-digest` (15:00 UTC) when Celery is running (Fly worker sets `SKIP_CELERY=1`)
3. GitHub Action `.github/workflows/cal-daily-digest.yml` (15:05 UTC backup)

Web does **not** start a digest thread unless `CAL_DAILY_DIGEST_WEB_BACKUP=1`. All senders call `send_cal_daily_digest`, which claims the calendar day with Redis SET NX before sending.

Copy is Jobs-path (matcher / kept jobs / applications) plus a Cal-frozen one-liner. Do not attach the SIGNAL industry brief.

## Manual send (terminal only)

```bash
curl -sS -X POST "$RFR_API_BASE/api/v1/market-graph/daily-digest-send" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: $RFR_ADMIN_KEY" \
  -d '{"force": false, "period_hours": 24}'
```

## Forbidden

- `--provider ai-gateway` / `--provider openai` / `--provider anthropic`
- Browsing api.openai.com, console.anthropic.com, or vercel.com/ai
- Drafting the email body with an LLM
- Keeping a Hermes cron that wraps this skill in an LLM provider
