# Outcome — Daily orchestrator cycle (2026-06-28)

**Agent:** Orchestrator (ProductSurface build)
**Status:** complete
**Type:** build

## Snapshot (before)

`python3 scripts/harness_snapshot.py` → `reports/harness_snapshot_latest.json` (generated 2026-06-28T19:41Z)

| Signal | Value |
|--------|-------|
| `api.pipeline.cache_pending` | **true** (`built_at: null`, `leads_count: 0`) |
| `api.homepage.hot_leads_count` | 46 |
| `api.summary` | 3,957 leads (319 hot / 1,686 warm / 1,952 cold); 4,326 companies; 12,231 signals |
| `database.telemetry.status` | **unavailable** — `psycopg2.OperationalError: Network is unreachable` (Supabase 6543) |
| `intelligence.*` (junk_reasons, gap_frequency, buyer_intent_gate, industry_top) | **unavailable** (DB unreachable from sandbox) |
| Alerts | `pipeline feed empty`, `DB telemetry unavailable` |

## Mission selection

Priority-2 (pipeline trust) blocker present: empty live feed + `cache_pending: true`.

**Acceptance step — cache refresh attempted, blocked by environment:**
- `python3 scripts/refresh_pipeline_cache.py --remote --wait` → **HTTP 403** `Admin access required — unknown email is not in ADMIN_EMAILS`. The `.env` `ADMIN_KEY` is a non-admin Supabase JWT, not the server's raw `ADMIN_KEY` secret.
- Local DB path also impossible: Supabase `db.*:6543` is **network-unreachable** from this sandbox.
- **Conclusion:** cache rebuild cannot be performed from this runner; it must come from the credentialed daily harness / prod scheduler. Documented as a follow-up.

**Verified the empty cache is NOT an active value-first emergency** (funnel is resilient):
- `/pipeline` already falls back to `/api/leads?limit=50&sort=score&exclude_junk=true` → returns 26 real scored buyers (Prologis, …) with `suggested_pipeline_action` + `robot_types_needed` on all 26/26.
- Home hero (`HeroLivePipeline`, `HeroSpotlightLeads`) reads `/api/leads/homepage` (46 hot, healthy) with static fallbacks.

## Build shipped (one mission)

**Value-first empty-state on `/pipeline`** — when the durable feed is empty *and* the fallback misses (today's exact `cache_pending` failure mode), the anonymous user previously hit a trust-killing dead end: a gray *"Pipeline data is syncing… Reload in a moment."* That violates `value_first_principle.md` ("Empty pipeline … kills trust permanently").

Replaced with an engaged, value-first card (`pages/Pipeline.tsx`):
- Reassurance framed around the buyer ("Live pipeline is rebuilding — your buyers are still here").
- **Live market totals** (`{hot} hot · {warm} warm robot buyers scored across {total} tracked accounts`) sourced from the summary that *does* load via the homepage fallback — proof the data is real while the ranked feed paints.
- **Two in-funnel CTAs** keep the user moving instead of bouncing: `Browse live buyer signals → /signals` and `Scan a company URL → /results`.

Reuses existing in-scope vars (`hotDeals`, `warmDeals`, `dbTotal`, `formatMetric`, wouter `Link`) — no new data deps, no new endpoints.

## Verification

- `tsc --noEmit` (frontend `check`): _see commit gate below_
- Lead-quality gates (`harness/gates.yaml`): not applicable — no backend lead-filter/junk code touched.

## Metrics delta

DB/intelligence deltas unavailable this cycle (telemetry down from sandbox). Pipeline-cache metrics unchanged (`cache_pending` still true — refresh blocked by env, not by code).

| Metric | Before | After |
|--------|--------|-------|
| Anonymous `/pipeline` empty-state | Dead "reload" message | Live totals + 2 in-funnel CTAs (value-first) |
| `cache_pending` | true | true (refresh requires credentialed runner) |

## Follow-ups

1. **[P1] Pipeline cache rebuild** — runner lacks DB reachability and an admin `ADMIN_KEY`. Ensure the scheduled daily harness (GitHub Actions / prod) has a real admin key or DB route; consider a prod-side post-deploy cache hook so `cache_pending` self-heals.
2. **[P2] Harness venv / network** — `database.telemetry: unavailable` blocks the whole `intelligence` slice from this environment. Either run the daily cycle where Supabase is reachable, or add an API-only intelligence fallback (junk/gap stats via admin API) so missions aren't blind when the DB route is down.
3. **[P3] ADMIN_KEY hygiene** — `.env` `ADMIN_KEY` is a Supabase JWT for a non-admin email; refresh script's remote path is unusable until it's the raw server secret.
