# Outcome: Snapshot DB telemetry

**Date:** 2026-06-23
**Agent:** PipelineHealth
**Result:** success
**Commit:** (this commit)

## Changes

- Added `scripts/harness_env.py` — centralized dotenv + `HARNESS_DATABASE_URL` override
- Snapshot now emits `database.telemetry` and prints connection/intelligence status on CLI
- Mission runner + notify load harness env at startup

## Metrics (before → after)

| Metric | Before (17:27Z snapshot) | After |
|--------|--------------------------|-------|
| `database.telemetry.status` | missing (`database: null`) | `connected` (source: dotenv) |
| `intelligence.junk_reasons.available` | false | **true** (6% junk in recent sample) |
| `intelligence.gap_frequency.available` | false | **true** (34 candidates; top gap: low_signals 17) |
| `industry_top[0]` | n/a | Unknown **960** (with signals) |
| Quarantined companies | n/a | **1,053** |
| Unknown industry w/ signals | n/a | **960** |

## Live friction signals (first DB-backed baseline)

- **Pipeline surface gaps:** `low_signals` (17) > `industry` (11) > `crm_descriptors` (5)
- **Recent-name junk sample:** 6% rate — dominated by OEM/vendor patterns (not the 69% CSV sweep; different population = recent ingest)
- **Industry concentration:** Unknown (960) >> Logistics (385) >> Hospitality (258)

## Follow-ups

1. **Rank 2:** `buyer-intent-gate-triage` — address no-intent rows at ingest (CSV sweep showed 69% of junk)
2. **Rank 3:** `rss-html-strip-and-report-filter` — attack Unknown industry noise
3. Set `HARNESS_NOTIFY_EMAIL` in `.env` so autonomous missions email the operator

## Verification

```bash
python3 scripts/harness_snapshot.py
# expect: DB telemetry: connected (dotenv)
# expect: Intelligence: junk=True gaps=True industries=15
```

No deploy required.
