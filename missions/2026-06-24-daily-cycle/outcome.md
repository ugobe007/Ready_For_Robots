# Outcome: Daily orchestrator cycle — 2026-06-24

**Agent:** Orchestrator (PipelineHealth flavor)
**Status:** done
**Type:** build / harness-reliability

## What shipped

Hardened `scripts/refresh_pipeline_cache.py --remote` so the daily harness
**fails fast and loud on auth/HTTP errors** instead of masking them as a
20-minute `--wait` timeout.

- New `_post_remote_refresh()` captures the HTTP status via `curl -w` (plain
  `curl -sS` exits 0 on a 401/403, so the old code treated auth failures as
  success and then polled uselessly until `--wait-timeout`).
- New `_should_wait_after_post()` — only poll for a rebuilt cache on a 2xx.
- New `_auth_header_args()` — routes a JWT-shaped ADMIN_KEY (`eyJ…`) to
  `Authorization: Bearer` (the server **always** rejects JWTs sent via
  `X-Admin-Key`); the raw secret still goes in `X-Admin-Key`.
- On 401/403 it now prints an actionable fix (sync the real `ADMIN_KEY`
  secret / use an admin Bearer token) and returns 1 immediately.
- Added `tests/test_refresh_pipeline_cache.py` (5 tests).
- Fixed pre-existing stale assertion in
  `tests/test_lead_filter_junk.py::test_ontology_descriptor_names_fail_logic_engine`
  (2 cases): names are still correctly junked (`ok is False`); the validator
  just added a newer `headline shape` reject reason the test didn't list.
  No behavior change — restores the `lead_quality_smoke` commit gate to green.

## Why this (north-star alignment)

The pipeline feed is empty in prod (`built_at: null`, `cache_pending: true`,
`leads_count: 0`) — the #1 snapshot alert and bet #2 (live actionable
surface). The acceptance criteria require running the remote refresh. Doing so
surfaced the root cause: **the automated refresh path was silently failing
auth and then timing out**, so the daily GitHub Action (14:00 UTC, calls the
identical `--remote --wait`) never rebuilt the cache and never reported why.
This is the same class of meta-friction as theme 0 (telemetry blind spot):
a "Done" automation that silently degrades. Fixing the harness so it reports
the real blocker is the highest-impact action available from this sandbox.

## Metrics — before / after

| Signal | Before | After |
|--------|--------|-------|
| `refresh_pipeline_cache --remote` on auth failure | prints 401, then polls full `--wait-timeout` (~20 min) → misleading "timed out" | fails in <1s with HTTP status + actionable fix, exit 1 |
| JWT-shaped ADMIN_KEY | sent via `X-Admin-Key` → always rejected | routed to `Authorization: Bearer` |
| `lead_quality_smoke` gate | **2 failed**, 177 passed (pre-existing drift) | **179 passed** |
| New refresh unit tests | none | 5 passing |

Snapshot intelligence deltas: **not measurable this cycle** — DB telemetry is
unreachable from this environment (`psycopg2.OperationalError: Network is
unreachable` to Supabase over IPv6), so `junk_reasons`, `gap_frequency`,
`buyer_intent_gate`, and `industry_top` all report `available:false`. This is
an environment/network limitation, not a code regression.

## Gates run

- `tests/test_refresh_pipeline_cache.py` — 5 passed (new)
- `lead_quality_smoke` (`test_lead_filter_junk.py` + `test_buyer_intent_gate.py`) — **179 passed**
- `partnership_rule` — included in the above, passing
- `tests/test_secondary_pass_cache_refresh.py` — passing
- End-to-end: `refresh_pipeline_cache.py --remote --wait` now returns
  `HTTP 403 — unknown email not in ADMIN_EMAILS` in <1s (was a 20-min hang).

## Blockers / follow-ups

1. **P0 — prod pipeline feed still empty.** The cache refresh is blocked in
   this environment: the `.env` `ADMIN_KEY` is a 219-char Supabase
   service_role/anon **JWT**, not the server's raw `ADMIN_KEY` secret, and
   there is no `SCRAPER_CRON_TOKEN`. The admin endpoint needs the real secret
   or an admin user Bearer token. **Action for a privileged runner:** set the
   correct `ADMIN_KEY`/cron token in the daily harness env (GitHub Actions
   secret + local `.env`), then `python3 scripts/refresh_pipeline_cache.py
   --remote --wait`. The script now reports this clearly instead of timing out.
2. **DB telemetry unreachable from CI/sandbox** — the snapshot `intelligence`
   slice cannot populate without direct Supabase reach. Consider an
   API-backed telemetry fallback (the `/api/.../summary` endpoint works) so
   junk/gap trends survive when the DB is firewalled.
3. **No deploy required** — change is CLI-script + test only; nothing runs on
   Fly. Committed + pushed; `fly deploy` intentionally skipped.

## North-star order check

names/events → scores → rank → robot specs. This mission unblocks the
**measurement + refresh loop** (prerequisite to all of the above), and the
lead-filter gate fix protects the names/events junk filters. No ranking or
copy tuning attempted while the feed/telemetry are dark — correct per order.
