# Outcome: conversion-cal-curiosity

**Date:** 2026-08-13  
**Status:** shipped on Fly; Vercel re-auth needed for custom-domain project

## Diff summary

### Cal voice (server)
- Rewrote buyer variants in `app/services/agent_messaging.py` to short curiosity-peer notes (~90–110 words)
- Curiosity subjects; removed Robert/RFQ first-touch closes
- Expanded `CAL_BANNED_PHRASES` / persona rules; updated `docs/cal_persona_spec.md`
- Hermes opener phrasing: “noticed … hiring … that timing caught my eye”
- Tests: `tests/test_cal_voice.py`, `test_cal_draft_guard.py`, `test_context_reason.py`, `test_ladder_cadence.py`, `test_cal_hermes_priority.py` — **35 passed**

### Conversion framing (client)
- `AnonymousValueStrip`, `PipelineOutreachValuePanel` — “What Cal would send — notice the timing”
- `pipelineLeadMap.ts` + `agentMessaging.ts` — anonymous drafts now Cal-voice (was “Hey / Find Companies Ready For Robots”)
- Home + Signup outcomes copy vs contact-list tools

### Digest winners → Cal pool
- Script: `scripts/prioritize_digest_winners_cal.py`
- Live overlays accepted (7): PFG `#941`, Medline `#4756`, DHL `#348`, HelloFresh `#11034`, FedEx `#407`, Apple `#11058`, GM `#11057`
- `CAL_INCLUDE_BUYING_WINDOW` **not** set on Fly (default off)

### Deploy
- Fly `ready-2-robot` deployed successfully (includes Vite frontend build in Docker image — UI + Cal templates live on https://ready-2-robot.fly.dev/)
- Vercel CLI token invalid (`vercel login` needed) — if custom domain still points at Vercel project `ready-for-robots`, re-auth and `vercel --prod` from `readyforrobots-new/`
- Buying-window flag remains off

## Golden samples (manual review)

### Performance Food Group — `bottleneck_first`

**Subject:** the boring food distribution workflow that usually matters

> Hi Performance Food Group, this is Cal.
>
> Quick field pattern in food distribution: the hours usually hide in receiving, replenishment, pallet moves, inventory exceptions, and returns, while everyone demos picking.
>
> The fastest AMR on the floor is rarely the one that survives real peak volume.
>
> If that rings true for Performance Food Group, I would be curious what you would put on that list first. If it does not, I am wrong — and that is useful too. Vendor-neutral either way.
>
> If you had to pick one warehouse workflow tomorrow, what would you put first?
>
> — Cal  
> Deployment Advisor, Ready For Robots

**Verdict:** Timely / curious — not a pitch.

### Medline — `what_survives`

**Subject:** what still looks good six months later in healthcare / distribution

> Hi Medline, this is Cal.
>
> Reaching out with one note for Medline.
>
> In healthcare / distribution, the deployments that still look good six months later almost always started with one owned bottleneck — not a demo-floor shortlist.
>
> … No pitch — just curious whether you are already past that step…
>
> — Cal  
> Deployment Advisor, Ready For Robots

**Verdict:** Exploration tone; invites “not yet.”

## Follow-ups

1. Confirm Vercel production URL matches Fly frontend (if custom domain still on Vercel)
2. Next Cal autonomy cycle regenerates CRM drafts with new templates (stale refresh)
3. After 1–2 weeks of buying-window overlay quality, consider `CAL_INCLUDE_BUYING_WINDOW=1`
4. Watch signup starts from `/pipeline` this week
