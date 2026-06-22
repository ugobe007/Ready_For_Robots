# Outcome: Friction baseline (intelligence)

**Date:** 2026-06-23
**Agent:** FrictionMiner (+ ProductThesis synthesis), Orchestrator
**Status:** complete
**Type:** research (one harness-config fix; no production/app code; no deploy)

## Headline

The friction baseline is now **live-DB-backed** for the first time — but only after fixing
the meta-friction (theme 0). The "DB telemetry" mission had been marked Done, yet the live
snapshot was **silently degraded**: `.venv-harness` was missing the libraries the
`intelligence` slice needs. All three sub-slices read `available:false` despite a valid
Postgres `DATABASE_URL` in `.env`.

Fixed by installing the four deps into `.venv-harness` and **pinning them** in a new
`harness/requirements.txt` so the slice cannot silently regress again.

### Telemetry restore chain (each install unblocked one sub-slice)
| Missing dep | Symptom before | Slice unblocked |
|-------------|----------------|-----------------|
| `sqlalchemy` + `psycopg2-binary` | `database.telemetry: unavailable (No module named 'sqlalchemy')` | `database.telemetry`, `industry_top` |
| `requests` | `junk_reasons.error: No module named 'requests'` | `junk_reasons` |
| `fastapi` | `gap_frequency.error: No module named 'fastapi'` | `gap_frequency` |

Result: `Intelligence: junk=True gaps=True industries=15` (was `junk=False gaps=False industries=0`).

## Top 5 friction themes (evidence-cited)

0. **Telemetry blind spot (meta) — RESOLVED.** Live slice was `available:false` across the
   board due to venv dep drift. Fixed + pinned (`harness/requirements.txt`). *A "Done"
   telemetry mission regressed at the venv layer with zero code change.*
1. **Robotics vendor / OEM contamination — dominant recent-flow leak.** Live junk sample
   (400 recent companies) = **5.8% junk, 100% vendor/OEM** (17 `robotics vendor / OEM` +
   6 `name pattern matches automation/robotics vendor`). It is the *only* junk class still
   entering fresh ingest. Anti-bet violation.
2. **RSS/HTML + market-report → Unknown industry.** **960** live Unknown-industry companies
   with signals — the #1 industry bucket, > 2× Logistics (385). Driven by HTML boilerplate
   (`nbsp` 3,557, `font` 3,343, `href`, `6f6f6f`, `indexbox`) + report spam (`market
   analysis/forecast/size/trends`, `... to 2035`). 1,110/3,163 (35%) of the CSV sweep.
3. **No buyer-intent signal — bulk backlog.** **2,188/3,163 = 69%** of the historical junk
   sweep: `buyer opportunity gate: no buyer-intent signal found`. Largest by volume, but a
   backlog cleanup — not what recent ingest produces.
4. **Headline fragments / verb-merge / mis-attributed names.** `invalid_name` bucket = 80
   rows; 8 `company name not found in signal text` (e.g. JLL). `Tesla moves`, `Lululemon
   claps`, one-off titles (`Ted Danson`, `Iran war`).
5. **Partnership compounds — recurring.** **58** quarantined across three 2026-06-22 sweeps
   (30/14/14). Real entity+entity (`Serve Robotics and White Castle`) + slogan noise
   (`Shaping Biotech And Life Sciences`, `Flying Taxis And Self-Driving Trucks`).

(Also: live pipeline feed **empty** — `cache_pending`, surface `lead_count: 0`,
`robot_types: []`; gap scan `low_signals` 17 + `industry` 11 dominate 34 candidates.)

## Top 5 ranked build missions (re-ranked from live slice)

| Rank | Mission | Agent | Why |
|------|---------|-------|-----|
| 1 | `vendor-oem-suppression-refresh` | LeadQuality | **Promoted.** 100% of recent junk; only class still entering pipeline; small blocklist surface. |
| 2 | `rss-html-strip-and-report-filter` | LeadQuality | 960 live Unknown (largest bucket); HTML + report spam. Biggest classifiable cleanup. |
| 3 | `buyer-intent-gate-triage` | LeadQuality | 69% of historical backlog junk. Suppress/route + instrument gate. |
| 4 | `partnership-quarantine-sweep` | LeadQuality | 58 recurring partnership compounds. |
| 5 | `industry-rescue-ontology` | LeadQuality | `industry` gap #2 (11/34) once RSS noise removed. |

(New addition `pipeline-cache-refresh-health` (PipelineHealth) ranked 6 — feed empty blocks surface work.)

## Metrics delta (snapshot)

| Metric | Before this mission | After |
|--------|--------------------|-------|
| `database.telemetry.status` | `unavailable` | `connected` |
| `intelligence.junk_reasons.available` | `false` | `true` (5.8% junk, OEM/vendor) |
| `intelligence.gap_frequency.available` | `false` | `true` (34 candidates) |
| `intelligence.industry_top` | `[]` (0) | 15 industries (Unknown 960 …) |
| Snapshot line | `junk=False gaps=False industries=0` | `junk=True gaps=True industries=15` |

## Quarantine / rectification sample (no `--apply`, read-only)

- `pipeline_junk_cleanup_20260619_222706.csv` (3,163 rows): buckets `display_junk` 2,311,
  `ok`/quarantined 772, `invalid_name` 80. Reasons: 69.2% no-intent, 3.1% seller/vendor
  story, 2.1% vendor/OEM, 0.3% mis-attributed fragment.
- `partnership_compound_quarantine_2026-06-22` ×3: 30 + 14 + 14 = 58 `would_quarantine`.
- `unknown_industry_keyword_analysis.txt`: 1,389 leads, HTML-token + report-spam dominated.

No quarantine scripts were run (research mission; `--apply` out of scope).

## Changes committed

- `docs/market_thesis.md` — Friction themes (theme 0 resolved; vendor/OEM = recent-flow
  leak), live Intelligence baseline table, re-ranked build backlog, header.
- `harness/requirements.txt` — **new**; pins `sqlalchemy`, `psycopg2-binary`, `requests`,
  `fastapi` so the intelligence slice does not silently regress.

## Follow-ups / open blockers

1. **Pipeline feed empty** (`cache_pending`) — surface tier/robot_types unmeasurable.
   Hand to PipelineHealth (`pipeline-cache-refresh-health`). Heed red line: no parallel
   local+Fly cache refresh.
2. Add `python3 -m pip install -r harness/requirements.txt` to harness bootstrap / README so
   a fresh `.venv-harness` is telemetry-ready.
3. Next execution mission should be **rank 1 `vendor-oem-suppression-refresh`** — highest
   leverage on live flow, now measurable via `junk_reasons`.
4. Re-trend `junk_reasons` / `industry_top` next mission now that the slice is live (deltas
   will be meaningful run-over-run).

## Deploy

None. Research mission; the only change is harness config + docs (no app/production code).
