# Outcome: Friction baseline (intelligence)

**Date:** 2026-06-23
**Agent:** FrictionMiner (+ ProductThesis synthesis)
**Status:** complete
**Type:** research (no production code; doc-only)

## Summary

Established the Phase 1 friction baseline from sweep reports because the snapshot's
DB-derived intelligence slice was unavailable. Updated `docs/market_thesis.md`
**Friction themes** (now evidence-backed) and **Ranked build backlog** (re-ranked by
volume × north-star order). No deploy — research mission, doc-only change.

## Metrics cited (baseline)

Snapshot `reports/harness_snapshot_latest.json` (generated 2026-06-22T17:27Z, pipeline built 17:15Z):

| Metric | Value |
|--------|-------|
| Companies in DB | 4,257 |
| Signals in DB | 11,841 |
| Tiers | hot 306 / warm 1,639 / cold 1,935 (total 3,880) |
| Pipeline surface leads | 9 (all tier `unknown`, `robot_types: []`) |
| Homepage hot leads | 47 |
| `intelligence.junk_reasons` | **available: false** (DB null) |
| `intelligence.gap_frequency` | **available: false** (DB null) |
| `intelligence.industry_top` | `[]` (DB null) |

Sweep-report sample (source of friction quantification):

| Report | Rows | Key finding |
|--------|------|-------------|
| `pipeline_junk_cleanup_20260619_222706.csv` | 3,163 | 2,188 (69%) no buyer-intent; 1,110 (35%) `Unknown` industry |
| `buyer_opportunity_junk_20260618_220744.csv` | 2,206 | mostly `company_name`-bucket no-intent |
| `partnership_compound_quarantine_*` (06-22) | 58 (30+14+14) | recurring vendor+entity + slogan compounds |
| `unknown_industry_keyword_analysis.txt` | 1,389 leads | top tokens = HTML boilerplate + market-report spam |

## Top 5 friction themes (evidence-backed)

0. **Telemetry blind spot** — snapshot intelligence DB slice `available:false` (no `DATABASE_URL`); harness can't self-measure friction. *Meta — fix first.*
1. **No buyer-intent signal** — 2,188/3,163 = **69%** of junk. Real-ish companies, no actionable event. Largest by volume.
2. **RSS/HTML + market-report noise → Unknown industry** — 1,110/3,163 = **35%** `Unknown`; tokens dominated by `nbsp/font/href/indexbox` and `market forecast/size/trends`.
3. **Robotics vendor/OEM contamination** — ~**167** vendor/seller flags; recurring Tesla/Foxconn/SoftBank/Nvidia. Anti-bet leak.
4. **Headline-fragment / verb-merge names** — `Tesla moves`, `Lululemon claps`, `Olympic goalie shares`, mis-attributed fragments (JLL).
5. **Partnership compounds** — 58 quarantined across three 06-22 sweeps despite shipped rule.

## Top 5 ranked build missions (new backlog)

1. `snapshot-db-telemetry` (PipelineHealth + Deploy) — wire read-only `DATABASE_URL` so intelligence slice populates. Unblocks all trending.
2. `buyer-intent-gate-triage` (LeadQuality) — suppress/route the 69% no-intent rows; instrument the gate.
3. `rss-html-strip-and-report-filter` (LeadQuality) — strip HTML boilerplate + demote market-research headlines; recovers 1,110 `Unknown` rows.
4. `vendor-oem-suppression-refresh` (LeadQuality) — extend OEM blocklist (~167 leaks).
5. `partnership-quarantine-sweep` (LeadQuality) — recurring sweep + harden rule for vendor+entity & slogan phrases.

## Dry-run / quarantine note

No `--apply` quarantine scripts were run. Findings are read-only aggregates over
existing `reports/` CSVs; the 58 partnership rows are already-quarantined records
from prior 06-22 sweeps, not new actions taken in this mission.

## Follow-ups / blockers

- **Blocker for trending:** until `snapshot-db-telemetry` (rank 1) ships, friction deltas
  cannot be auto-tracked; next research mission must again reconstruct from CSVs.
- Confirm whether `_db_session` should accept a read-replica URL distinct from the
  app's primary `DATABASE_URL` (snapshot is read-only).
- Re-run `harness_snapshot.py` with DB access after rank 1 to capture the first real
  `junk_reasons`/`gap_frequency` baseline.

## Files changed

- `docs/market_thesis.md` — Friction themes + Ranked build backlog (evidence-backed)
- `missions/2026-06-23-friction-baseline/outcome.md` — this file

## Verification

Doc-only mission; no code paths touched → no pytest gate applicable. No deploy.
