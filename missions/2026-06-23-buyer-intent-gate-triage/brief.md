# Mission: Buyer-intent gate triage

**Date:** 2026-06-23
**Agent:** LeadQuality
**Status:** done
**Type:** build

## Goal

Instrument the buyer-opportunity gate and triage the ~69% no-intent junk bucket: stamp telemetry on `crm_metadata`, optionally quarantine rows that fail buyer-intent evidence but are not known buyer brands.

## Acceptance criteria

- [ ] `app/services/buyer_intent_gate.py` — structured assess + stamp
- [ ] `scripts/buyer_intent_gate_triage.py` — dry-run, `--stamp`, `--apply`
- [ ] Harness snapshot includes `intelligence.buyer_intent_gate` sample stats
- [ ] Tests in `tests/test_buyer_intent_gate.py`
- [ ] Dry-run report with counts; `--stamp` on sample batch for telemetry baseline
- [ ] Commit, push, notify — deploy only if API behavior change requires it

## Context

Friction baseline rank-1 backlog item. Gate logic lives in `lead_filter._buyer_opportunity_gate`; classify_lead already marks these as display junk. Triage removes them from secondary-pass pools via quarantine when appropriate.

Read `docs/market_thesis.md` intelligence baseline (960 Unknown industry rows).

## Out of scope

- Rewriting the entire gate regex set (small targeted additions OK if tests prove a gap)
- Hard deletes
- Parallel pipeline cache refresh

## Autonomous policy

Commit, push, notify when done. Run `--apply` only after dry-run summary in outcome.md unless sample size ≤ 50 and counts match expectations.
