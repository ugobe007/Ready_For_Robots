# Outcome: Pipeline observe baseline

**Date:** 2026-06-22
**Agent:** PipelineHealth (Orchestrator-driven, observe-only)
**Status:** complete (DRAFT — not committed)

## What ran

- `python3 scripts/harness_snapshot.py` → wrote `reports/harness_snapshot_latest.json`
  (and timestamped `harness_snapshot_20260622_160306.json`). **No production code touched.**
- Snapshot generated_at: `2026-06-22T16:03:04Z`. API base: `https://ready-2-robot.fly.dev`.

## Baseline metrics

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Pipeline `built_at` | `2026-06-22T15:56:10Z` | — | — |
| Cache age at snapshot | **6.9 min** | stale > 6 h | ✅ fresh |
| `cache_pending` | `null` | — | ✅ idle |
| Anonymous pipeline `leads_count` | **9** | min 1 | ✅ healthy |
| Anonymous `visible_count` | 9 | — | ✅ |
| Homepage `hot_leads_count` | **47** | min 1 | ✅ healthy |
| Summary total / hot / warm / cold | 3909 / 306 / 1652 / 1951 | — | — |
| `junk_filtered` | 37 | — | ⚠️ see below |
| Companies in DB / signals in DB | 4282 / 11809 | — | — |
| Alerts raised | **0** | — | ✅ |

Git: branch `main`, commit `16a7a95`, worktree **dirty (24 files)** — pre-existing, unrelated to this mission.

## Assessment

**Is the cache fresh?** ✅ Yes. Built 6.9 minutes before snapshot; `cache_pending` is null. Well inside the 6-hour stale window.

**Is the anonymous feed healthy?** ✅ Yes, but thin. Pipeline serves 9 leads to anonymous users and homepage exposes 47 hot leads — both above the min-1 alert floor. No empty-feed risk. The 9-lead anonymous slice is by design (entitlement-gated) and is not an alert condition.

**North-star read (names/events first):**
- The summary shows **340 leads in the `"New"` industry bucket** (the largest single category, ahead of Logistics 324). "New"/uncategorized is the classic smell for unclassified or low-quality `companies.name` rows — exactly the layer-1 "names & events" concern the north star says to fix before tuning rank or robot specs.
- **`junk_filtered` = 37** against `total_signals` 7783 (~0.5%). That filter rate looks low; either the corpus is unusually clean or the junk filter is under-catching partnership/headline-merge rows. Worth a LeadQuality audit, not a code change in this mission.

## Tooling note (non-blocking)

`database` block reports `No module named 'sqlalchemy'` — the snapshot's optional direct-DB queries can't run in this environment. API-derived metrics are unaffected. Flag for a future harness setup task (install deps or gate the optional DB path); not a production issue.

## Recommended next mission (pick ONE)

**→ LeadQuality: audit the `"New"`/uncategorized bucket and junk-filter coverage.**

Rationale tied to north star: priority 1 is *names & events*. The 340-row `"New"` bucket plus a ~0.5% junk-filter rate are the strongest signals in this baseline that layer-1 quality may be leaking. Per the strict rule ("never tune rank/specs while names are broken"), this outranks any ProductSurface or Deploy work. A dry-run audit (no `--apply`) of `app/services/lead_filter.py` quarantine candidates and the "New" companies would confirm or clear the concern before any scoring/rank effort.

Deferred (not now):
- **ProductSurface** — anonymous feed is healthy; hero ticker swap is explicitly out of scope and a separate mission.
- **Deploy** — nothing to ship; worktree is dirty with unrelated changes.

## Acceptance criteria

- [x] `scripts/harness_snapshot.py` runs successfully
- [x] `reports/harness_snapshot_latest.json` documents `built_at`, lead counts, alerts
- [x] Brief assessment: cache fresh ✅, anonymous feed healthy ✅
- [x] One follow-up mission recommended (LeadQuality) with north-star rationale

## Guardrails honored

No code changes · no git commit/push · no fly deploy · no `--apply` scripts · `reports/` not committed.
