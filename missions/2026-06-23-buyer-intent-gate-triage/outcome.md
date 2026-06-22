# Outcome: Buyer-intent gate triage

**Date:** 2026-06-23
**Agent:** LeadQuality
**Result:** success
**Type:** build

## Summary

Instrumented the buyer-opportunity gate with structured assessment, triage script, harness snapshot metrics, and tests. Dry-run on recent 200 active companies shows **97 no-intent** / **98 quarantine-route** rows (55% of assessed population). Stamped **177** rows with `crm_metadata.buyer_intent_gate` for trending. Mass `--apply` quarantine deferred — review dry-run CSV first.

## Changes

- `app/services/buyer_intent_gate.py` — assess, stamp, route (`pass` | `secondary` | `quarantine`)
- `scripts/buyer_intent_gate_triage.py` — dry-run / `--stamp` / `--apply`
- `scripts/harness_snapshot.py` — `intelligence.buyer_intent_gate` sample
- `tests/test_buyer_intent_gate.py` — 6 tests
- `harness/gates.yaml` — include new tests in LeadQuality smoke gate
- `requirements-harness.txt` — dotenv + httpx note for DB snapshot deps

## Dry-run metrics (limit=200, recent active companies with signals)

| Metric | Count |
|--------|-------|
| Assessed | 177 |
| no_intent | 97 |
| seller_story | 1 |
| quarantine route + classify junk | 98 |
| no_intent rate | ~55% |

Report: `reports/buyer_intent_gate_triage_20260622_182118.csv`

## Stamped

`python3 scripts/buyer_intent_gate_triage.py --stamp --limit 200` → **177** companies tagged.

## Follow-ups

1. Review CSV; run `--apply --limit 500` in batches to quarantine confirmed no-intent junk (not known brands).
2. Rank 2 backlog: `rss-html-strip-and-report-filter` (960 Unknown industry rows).
3. Re-run `harness_snapshot.py` to capture first `buyer_intent_gate` intelligence slice after stamp.

## Verification

```bash
python3 -m pytest tests/test_buyer_intent_gate.py tests/test_lead_filter_junk.py -q
python3 scripts/buyer_intent_gate_triage.py --limit 200
```

No deploy required (harness + DB metadata only).
