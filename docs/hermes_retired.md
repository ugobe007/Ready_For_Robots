# Hermes is retired

**Date:** 2026-08-26

Hermes was a Nous agent on a Mac (`~/.hermes/`), plus research cron and Fly ingest that fed Cal and SIGNAL. FIND never called it. It is not a product agent.

## What died

- Mac Hermes cron as if it were Jobs
- Fly ingest as a Jobs feed (`/api/v1/market-graph/*ingest*`, qualify overlays, buying-window / video overlays)
- Hermes Fly smoke that `--apply`s infer-qualify onto the public pipeline
- Cal buyer outreach as a product path (`CAL_AUTONOMY_ENABLED=0` and `ENABLE_SCHEDULED_CAL_AUTONOMY=0` in `fly.toml`). Scheduled draft create/refresh and due follow-ups stay paused with autopilot. The daily digest reports Jobs-path facts, not SIGNAL “opportunity signals.”
- Treating `/experiment` or Hermes research as FIND
- `--provider ai-gateway` leftovers (HTTP 402)

Ingest endpoints stay in the API so we do not force a migration. They return **410** unless `HERMES_INGEST_ENABLED=1`. Scripts refuse unless `HERMES_RETIRED_OVERRIDE=1`.

## What stayed

- Ontology (`ontology/`, `ROBOT_INFERENCE_RULES.md`)
- Fly matcher: `POST /api/robot-job-match` (`app/services/robot_job_matcher.py`)
- Market-graph loop for Jobs (tension / match cache). Do **not** set `MARKET_GRAPH_RUN_RESEARCH` or `LEAD_RESEARCH_AGENT_ENABLED`
- Harness ProductManager + verify-readyforrobots
- Jobs CRM (`/pipeline?src=jobs_activate`) and the signup wall

## Product loop

Robot URL on `/` → Job Cards → signup wall → CRM.

Cursor **pstack** is the site agent protocol plus IDE routing (How / Act / Critic). It does not replace the matcher and is not a customer chatbot. See [`pstack_jobs.md`](pstack_jobs.md).

Historical bridge notes: [`hermes_intelligence_bridge.md`](hermes_intelligence_bridge.md) (retired).
