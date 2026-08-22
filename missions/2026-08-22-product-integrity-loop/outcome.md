# Outcome — Product integrity loop

**Date:** 2026-08-22  
**Type:** build  
**Status:** shipped (awaiting merge)

## Vercel (why jobs did not land on production)

- GitHub **Deploy frontend to Vercel** skip-greened in 6–11s: `VERCEL_TOKEN` / `VERCEL_ORG_ID` / `VERCEL_PROJECT_ID` empty.
- Vercel Git built **Preview** URLs for PR branches. Merge commit `bca1e6f5` has Fly production only — no Vercel Production environment.
- `readyforrobots.com` and `ready-for-robots.vercel.app` both serve `index-bxLpnQiT.js`. Header-hide preview `3f1abc45` is a different bundle (`index-bDp8Nri6.js`) and was never promoted.
- Workflow now **fails** when secrets are missing so this cannot hide behind a green badge.

Owner action: add the three GitHub secrets, re-run **Deploy frontend to Vercel**, or promote the latest good Preview to Production.

## Diff

- Product Integrity loop docs + `ontology/rfr_product_loop.v1.json`
- ProductManager on the roster; compiled memory compiler
- Hourly observe workflow (no PR, no merge)
- `harness_daily.py` compiles memory after snapshot
- Tests: `tests/test_harness_compile_memory.py`

## Metrics

Compiler `next_mission` on this machine: `vercel-production-cli-secrets`.

## Follow-ups

Set Vercel CLI secrets. Then smoke FIND → cards → CRM on `readyforrobots.com`.
