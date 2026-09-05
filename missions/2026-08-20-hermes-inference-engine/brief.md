# Mission: Hermes uses RFR inference — no paid OpenAI/Anthropic

**Date:** 2026-08-20
**Agent:** LeadQuality + Deploy
**Status:** complete
**Type:** build

## Goal

Stop the Hermes agent from spending tokens on OpenAI, Anthropic, and Vercel AI Gateway. Company/URL lookups, qualify overlays, industry briefs, and the daily email digest must run on ReadyForRobots’ local inference engine (heuristic + evidence), not paid LLM APIs.

Trigger: cron `RFR daily email digest` failed HTTP 402 — Vercel AI Gateway credit balance.

## Acceptance criteria

- [x] `llm_json_completion` does not call OpenAI/Anthropic unless `RFR_ALLOW_PAID_LLM=1`
- [x] Company homepage OpenAI resolve is off (evidence URLs / local inference only)
- [x] Newsletter + industry brief skip paid LLM by default
- [x] `POST /api/v1/market-graph/infer-qualify` qualifies leads via `lead_inference_engine`
- [x] Daily digest Hermes skill curls Fly (Cal digest + heuristic brief) — no `--provider ai-gateway`
- [x] Targeted pytest passes
- [x] Docs/skills tell Hermes never to pin AI Gateway / Anthropic / OpenAI

## Out of scope

- Scout conversational chat (not a lookup)
- Force-push to `main`
- Committing `reports/`
