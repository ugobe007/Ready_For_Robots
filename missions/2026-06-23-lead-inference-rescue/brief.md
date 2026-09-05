# Mission: Lead inference gap rescue

**Date:** 2026-06-23
**Agent:** LeadQuality
**Status:** done
**Type:** build

## Goal

Close `lead_inference` gaps on existing pipeline companies by re-running inference without re-applying ingest buyer gate.

## Acceptance criteria

- [x] Skip `_buyer_opportunity_gate` when `is_new_company=False` (refresh path)
- [x] `_run_inference_rescue` accepts persisted `crm_metadata.lead_inference`
- [x] Secondary pass batch `--require-gap lead_inference`
