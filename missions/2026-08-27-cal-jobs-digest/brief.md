# Cal daily digest and worker match Jobs

**Date:** 2026-08-27  
**Type:** build  
**Agents:** Orchestrator, Deploy

## Goal

Cal’s daily email and worker must match the Jobs product. Autopilot/scheduled send stays off. Scheduled draft create/refresh pauses with autopilot. Digest reports Jobs-path facts or a Cal-frozen one-liner — not SIGNAL “opportunity signals.” Do not send due follow-ups or unfreeze HOT as a send list. Fix digest double-send.

## Acceptance

1. `CAL_AUTONOMY_ENABLED` and `ENABLE_SCHEDULED_CAL_AUTONOMY` stay `0` in `fly.toml`. Do not enable `MARKET_GRAPH_RUN_RESEARCH`, `HERMES_INGEST_ENABLED`, or `LEAD_RESEARCH_AGENT_ENABLED`.
2. When autopilot is off, scheduled `_draft_and_store` and due follow-ups no-op. Manual admin Run cycle still works and does not send held follow-ups.
3. Digest copy has Jobs-path counts (matcher / kept jobs / applications) and a Cal-frozen line. No industry brief / “sales teams prioritize accounts.”
4. Intros stay on the 0 path. HOT 300 is leftover queue copy, not a send list.
5. Digest send is claimed once per UTC day (Redis SET NX). Web does not start a digest thread unless `CAL_DAILY_DIGEST_WEB_BACKUP=1`.

## Out of scope

Fly deploy unless `fly.toml` flags change (they should already be 0). Re-enable buyer sales. Hermes ingest.
