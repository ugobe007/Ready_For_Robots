# Outcome: Lead inference gap rescue

**Date:** 2026-06-23
**Status:** done

## Root cause

`refresh_company_inference` re-ran `_buyer_opportunity_gate` on aggregated signal text, rejecting companies already on the pipeline surface. Rescue always returned `inference_rescue: failed`.

## Fix

- `lead_inference_engine._gate_lead_vs_junk(..., enforce_buyer_gate=is_new_company)` — skip article gate on refresh
- `_run_inference_rescue` also accepts persisted `crm_metadata.lead_inference`

## Batch results

- `--require-gap lead_inference --limit 50`: **2** fills (Boston LA, Multimillion-dollar Sheetz)
- Remaining gaps require broader scan / signal backfill on lower-score leads
