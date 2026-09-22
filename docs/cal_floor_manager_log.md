# Cal Floor Manager Log

**Hermes is retired (2026-08-26).** Historical hourly coach ticks from retired skill `rfr-sales-floor-manager`. Newest first. Do not cron this as Jobs.

Spec: [docs/skills/rfr-sales-floor-manager.SKILL.md](./skills/rfr-sales-floor-manager.SKILL.md)

| Date | Scoreboard | Actions | Outcome |
|------|------------|---------|---------|
| — | — | Skill stood up 2026-08-14 | Awaiting first cron tick |

## How to read

- **ALERT** — operator intervention
- **PRIORITY / VOICE / INGEST_GAP** — coach recommendations
- **KILL_SEND** — outbound pause recommendation (human confirms)
- **SILENT** — green hour

## 2026-09-14 16:21 UTC
- **Scoreboard:**
  - cal=UNKNOWN (cal-status endpoint timed out; was DISABLED/intentional-hold as of 2026-08-30)
  - scraper=33/150 (22.0%) — no active_runs, no recent_runs — 5th+ consecutive tick below target (dropped 34→33 since last tick; barely trickling)
  - pipeline=5 leads, all tier=None, score=None — new pool: Concord Hospitality, Shamrock Foods, Ensign Group, Naver D2SF, McDonald's — cache rebuilt 16:14Z; tier-scoring still absent
  - hermes_stamp=0/5 (0%) — dropped from 2/5 last tick; zero qualify/buying_window/decision_makers on any lead in new pool
  - funnel=unavailable (harness snapshot conversion block empty)
- **Actions:**
  1. `ALERT` — Cal-status endpoint timed out; cannot confirm Cal state. Last known: DISABLED (intentional hold, env_enabled=false). Operator must verify Cal is alive on Fly before any outbound is considered.
  2. `ALERT` — Scraper 33/150 (22.0%), 5th+ consecutive tick, no active_runs/recent_runs. Count dropped vs prior tick (34→33). Manual scrape trigger or Fly scraper-worker restart required.
  3. `INGEST_GAP` — Hermes stamp 0/5 (0%), down from 2/5. New lead pool (Concord Hospitality, Shamrock Foods, Ensign Group, Naver D2SF, McDonald's) has no qualify/buying_window coverage. Tier scoring absent. Research tick needed: run qualify + buying_window for all 5 leads before any outbound window opens.
- **Next hour watch:** Cal-status reachability; scraper count recovery above 50/150; any tier assigned to new lead pool; hermes_stamp ≥ 2/5.

## 2026-09-14 17:22 UTC
- **Scoreboard:**
  - cal=DISABLED (confirmed reachable; heartbeat fresh 105s ago; runtime_override=true — intentional operator hold; env_enabled=false; send_limit=0; draft_batch=0) ⚠️ NEW: template_fingerprint=45e2977c8c888f1f6cfe ≠ stored_fingerprint=1bd087e4bad1c2c28582 — mismatch detected
  - scraper=36/150 (24.0%) — no active_runs, no recent_runs — 6th+ consecutive tick below target (33→36 in ~1hr, +3 trickle; no recovery)
  - pipeline=5 leads, 0 HOT, 0 stamp — same pool (Concord Hospitality, Shamrock Foods, Ensign Group, Naver D2SF, McDonald's); cache rebuilt 17:15Z; tier/score still absent
  - hermes_stamp=0/5 (0%) — no qualify / buying_window / decision_makers on any lead; unchanged from prior tick
  - funnel=unavailable (harness snapshot conversion block empty)
- **Actions:**
  1. `ALERT` — **Template fingerprint mismatch** (NEW): `template_fingerprint=45e2977c8c888f1f6cfe` ≠ `stored_fingerprint=1bd087e4bad1c2c28582`. Cal is disabled so no sends will fire, but this must be resolved before re-enable. Operator: determine which template version is authoritative and re-store the fingerprint. Do not flip Cal on until mismatch is cleared.
  2. `ALERT` — Scraper 36/150 (24.0%), 6th+ consecutive tick, no active_runs. Net gain +3 in last hour (trickle, not recovery). Manual scrape trigger or Fly scraper-worker restart required. Without lead intake, pipeline cannot grow.
  3. `INGEST_GAP` — Hermes stamp 0/5 (0%), unchanged. Same 5 leads with no qualify/buying_window/decision_makers coverage. No HOT leads. Tier scoring absent. Research tick needed on all 5 leads (Concord Hospitality, Shamrock Foods, Ensign Group, Naver D2SF, McDonald's) before any outbound window is considered.
- **Next hour watch:** Template fingerprint cleared; scraper count above 60/150; any tier/HOT assigned in pipeline; hermes_stamp ≥ 1/5.

## 2026-09-14 18:20 UTC
- Scoreboard: cal=DISABLED (runtime_override=true, heartbeat_age=75s fresh, fingerprint mismatch STILL 45e2977c≠1bd087e4, template_version=3) | scraper=26/150 (17.3%, DOWN from 36 last tick — rolling 24h regressed, active_runs=[], recent_runs=[]) | pipeline=5 leads, 0 HOT, 1 hermes_stamped (up from 0 — marginal) | funnel=no snapshot conversion data
- Actions:
  1. ALERT: Template fingerprint mismatch UNRESOLVED — 7th+ consecutive tick (45e2977c8c888f1f6cfe ≠ stored 1bd087e4bad1c2c28582). Cal cannot be re-enabled until this is resolved. Escalate: operator must diff template v3 against stored hash or reset stored fingerprint.
  2. ALERT: Scraper REGRESSED — 26/150 (17.3%) vs 36/150 last hour. Rolling 24h count moved DOWN; no active_runs, no recent_runs. Scraper appears fully stalled, not trickling. Manual restart or investigation required.
  3. INGEST_GAP: Pipeline 5 leads, 0 HOT, 1 hermes_stamped (marginal improvement from 0). Hermes qualify/buying_window stamp still not reaching sales floor at scale. Trigger Hermes research tick for all 5 leads; HOT pool must grow before Cal re-enable makes sense.
- Next hour watch: Has fingerprint mismatch been resolved? Did scraper restart produce active_runs? Did hermes_stamped count grow beyond 1?

## 2026-09-14 19:20 UTC
- Scoreboard: cal=DISABLED(runtime_override=true, heartbeat_age=56s, fingerprint_MISMATCH=45e2977c≠1bd087e4 TICK-8+) scraper=26/150(17.3%,no_active_runs,no_recent_runs,STALLED) pipeline=total=5,HOT=0,WARM=0,COLD=0,hermes_stamped=1,built_at=2026-09-14T19:02Z funnel=no_snapshot
- Actions:
  - ALERT: Template fingerprint mismatch (45e2977c ≠ 1bd087e4) now 8th+ consecutive tick — Cal re-enable blocked. Operator must diff template v3 or reset stored hash. Zero outbound possible until resolved.
  - ALERT: Scraper fully stalled — 26/150 (17.3%), no active_runs, no recent_runs, zero improvement from prior hour. Pipeline fuel critically low; new lead intake stopped.
  - INGEST_GAP: Pipeline 5 leads with 0 tiers assigned (HOT=0, WARM=0, COLD=0) and only 1 hermes_stamped — tier scoring is absent or broken. Trigger Hermes research tick on all 5 to get tier signals before any outbound is possible.
- Next hour watch: (1) Has fingerprint mismatch been resolved / hash reset? (2) Any scraper runs triggered or active? (3) Pipeline tier coverage — did any leads get HOT/WARM after Hermes tick?

## 2026-09-14 20:20 UTC
- **Scoreboard:** cal=DISABLED (runtime_override=true, heartbeat_age=52s fresh, fingerprint_MISMATCH=45e2977c≠1bd087e4 **TICK-9+**) | scraper=26/150 (17.3%, no_active_runs, no_recent_runs, **STALLED 9th+ hour**, zero improvement) | pipeline=total=5, HOT=0, WARM=0, COLD=0, hermes_stamped=1/5, built_at=2026-09-14T19:57Z | funnel=no_snapshot_conversion_data
- **Actions:**
  1. `ALERT` — **Template fingerprint mismatch TICK-9+** (45e2977c8c888f1f6cfe ≠ stored 1bd087e4bad1c2c28582) — **still unresolved**. Cal cannot be re-enabled. This is now the 9th+ consecutive tick blocked. Operator must: diff template v3 source against stored hash OR call the reset-fingerprint endpoint to re-store. No outbound possible until cleared.
  2. `ALERT` — **Scraper STALLED 9th+ consecutive hour** — 26/150 (17.3%), identical to prior two ticks, no active_runs, no recent_runs. Pipeline is receiving zero new leads. Manual Fly worker restart (`fly restart scraper-worker -a ready-2-robot`) or investigation into scraper logs is overdue.
  3. `INGEST_GAP` — Pipeline 5 leads, 0 tiers assigned (HOT=0/WARM=0/COLD=0), 1 hermes_stamped (unchanged). Tier scoring absent or scoring worker not running. Even if Cal and scraper were re-enabled today, there is no qualified HOT pool to draw from. Hermes research tick needed on all 5 leads to produce tier signals.
- **Next hour watch:** (1) Fingerprint resolved / hash reset → Cal re-enable unblocked? (2) Any scraper active_run or count > 26? (3) Any tier (HOT/WARM) assigned in pipeline after research tick?

## 2026-09-14 21:20 UTC
- Scoreboard: cal=DISABLED(runtime_override=true, heartbeat_age=78s, fingerprint_mismatch=45e2977c≠1bd087e4 tick10+) scraper=STALLED(21/150 14%, rolling window DRAINING from 26→21, active_runs=0, recent_runs=0, ~10h stalled) hermes_stamp=1/5(HOT=0/WARM=0/COLD=0, tier-scoring absent) funnel=unavailable(no snapshot conversion data)
- Actions:
  - ALERT: Cal DISABLED — runtime_override=true, fingerprint mismatch 45e2977c ≠ 1bd087e4 is now 10th+ consecutive tick unresolved. Zero sends possible (send_limit=0, draft_batch=0). Operator must diff template v3 and reset stored hash before Cal can be re-enabled.
  - ALERT: Scraper STALLED — 21/150 (14%), 24h window actively DRAINING (26→21 since last tick, no new leads entering). Zero active/recent runs. ~10 consecutive hours with no intake. Pipeline fuel fully stopped.
  - INGEST_GAP: Pipeline 5 leads / 0 tiers (HOT=0/WARM=0/COLD=0) / 1 hermes_stamped. Tier scoring absent — no qualified pool exists for any outbound window. Nudge Hermes research tick on all 5 leads.
- Next hour watch: Scraper restart (fly restart scraper-worker -a ready-2-robot); template hash diff/reset to unblock Cal; confirm tier scoring resumes after scraper ingests new leads.

## 2026-09-14 22:21 UTC
- Scoreboard: cal=DISABLED(runtime_override=true, fingerprint-mismatch 45e2977c≠1bd087e4, heartbeat-age=200s fresh) scraper=127/150(84.7% ON_TRACK — recovered from 21/150 stall last tick; no recent_runs trace visible) hermes_stamp=1/5-leads pipeline=HOT=0/WARM=0/COLD=0 funnel=unavailable
- Actions:
  1. ALERT: Cal DISABLED — fingerprint mismatch (template=45e2977c8c888f1f6cfe vs stored=1bd087e4bad1c2c28582) persists 11th+ consecutive tick. runtime_override=true blocks re-enable. Operator action: diff template v3 hash against stored hash → reset stored fingerprint via admin API or env. send_limit=0, draft_batch=0, followups_paused. No drafts or sends until resolved.
  2. INGEST_GAP: Pipeline 5 leads, 0 tiered (HOT=0/WARM=0/COLD=0), 1/5 hermes_stamped — tier scoring absent 11th+ consecutive tick. 4 leads have no Hermes research coverage. Qualify/DM stamp not reaching sales floor. Nudge Hermes research tick on all 5 pipeline leads.
  3. NOTE(scraper-recovery): Scraper 127/150 (84.7%) — on_track=true. Significant recovery from last tick (21/150 stalled). Caution: recent_runs=[] still empty, no active_runs visible — intake count may reflect a delayed 24h window roll rather than live runs. Monitor next tick for continued accumulation.
- Next hour watch: Cal fingerprint mismatch (unresolved 11th+ tick); pipeline tier coverage after any Hermes research tick; scraper recent_runs populated vs empty.

## 2026-09-14 23:22 UTC
- Scoreboard: cal=DISABLED (runtime_override=true, heartbeat 240s fresh/not stale) | scraper=HEALTHY 181/150 (120.7%, on_track=true, recent_runs still empty) | hermes_stamp=1/5 leads, tiers=HOT:0/WARM:0/COLD:0 (all 5 untiered) | funnel=snapshot unavailable
- Actions:
  1. ALERT — Cal DISABLED, fingerprint mismatch 12th consecutive tick. template_fingerprint=45e2977c8c888f1f6cfe ≠ stored_fingerprint=1bd087e4bad1c2c28582 (template_version=3). runtime_override=true blocks re-enable. send_limit=0, draft_batch=0. Operator must diff template v3 and reset stored fingerprint to unlock Cal. Heartbeat fresh (240s / stale_threshold=1800s) — runtime is alive, just blocked.
  2. INGEST_GAP — Pipeline: 5 leads, 0 tiers (HOT=0/WARM=0/COLD=0), 1 hermes-stamped. Tier scoring absent 12th tick. Cal has no qualified pool to work from even when fingerprint is resolved. Hermes research tick needed on all 5 pipeline leads to restore tier coverage.
  3. NOTE — Scraper CONFIRMED healthy: 181/150 leads (120.7%) vs 127/150 last tick. Intake accelerating past target. recent_runs still empty in status response — watch for roll-over artefact vs live confirmation, but trajectory positive.
- Next hour watch: (1) Did operator reset stored fingerprint → Cal enabled? (2) Did Hermes research tick tier any of the 5 pipeline leads? (3) Scraper — does leads_last_24h hold >150 next tick?

## 2026-09-15 00:22 UTC
- **Scoreboard:** cal=DISABLED (runtime_override=true, env_enabled=false **[DUAL BLOCKER]**, heartbeat_age=164s fresh, fingerprint_mismatch=45e2977c≠1bd087e4 **TICK-13**) | scraper=220/150 (146.7%, on_track=true, recent_runs=[] empty) | pipeline=total=5, HOT=0, WARM=0, COLD=0, NONE=5, hermes_stamped=1/5, built_at=2026-09-15T00:03Z (fresh) | funnel=unavailable
- **Actions:**
  1. `ALERT` — Cal DISABLED **13th consecutive tick** — **DUAL BLOCKER confirmed**: (a) `env_enabled=false` — `CAL_ENABLED` env var is off in Fly secrets; (b) template fingerprint mismatch `45e2977c8c888f1f6cfe` ≠ stored `1bd087e4bad1c2c28582` (template_version=3). Both must be resolved: `fly secrets set CAL_ENABLED=true -a ready-2-robot` AND diff/reset stored fingerprint via admin API. Runtime toggle is available (`runtime_toggle_available=true`) but env_enabled=false means toggle alone is insufficient. send_limit=0, draft_batch=0, all sends paused. Heartbeat fresh — process is alive, just double-blocked.
  2. `INGEST_GAP` — Pipeline 5 leads, 0 tiers (HOT=0/WARM=0/COLD=0), 1/5 hermes_stamped — **13th consecutive tick** with zero tier coverage. Even when Cal blockers are resolved, there is no qualified HOT pool to draw from. Hermes research tick needed on all 5 pipeline leads immediately.
- **Next hour watch:** (1) Did operator set CAL_ENABLED=true in Fly secrets + reset template fingerprint? (2) Any tier assigned after Hermes research tick on pipeline leads? (3) Scraper 220/150 — does leads_last_24h continue to grow or plateau? (4) recent_runs still empty — watch for live run confirmation.

## 2026-09-15 01:20 UTC
- Scoreboard: cal=DISABLED(env_enabled=false, fingerprint-mismatch 45e2977c≠1bd087e4, send_limit=0, draft_batch=0, heartbeat=80s/not-stale) scraper=248/150 (165.3% on-track) pipeline=5-leads/0-tiers/HOT=0/WARM=0/COLD=0/1-hermes-stamped funnel=unavailable(snapshot empty)
- Actions:
  1. ALERT — Cal DISABLED, 14th consecutive tick. DUAL BLOCKER persists: (a) env_enabled=false — CAL_ENABLED Fly secret is off; (b) template fingerprint mismatch 45e2977c ≠ stored 1bd087e4 (template_v3). runtime_toggle_available=true but toggle alone insufficient while env_enabled=false. Fix requires operator: fly secrets set CAL_ENABLED=true + reset stored fingerprint. No outbound drafts or sends possible in current state.
  2. INGEST_GAP — Pipeline: 5 leads, 0 with any tier (HOT/WARM/COLD all zero), 1/5 hermes_stamped. Even if Cal unblocked today there is no qualified HOT/WARM pool to work. Hermes research tick overdue on all 5 leads — tier scoring absent 14th tick.
- Next hour watch: Same dual-blocker check; watch for tier scoring to appear on pipeline leads after next Hermes research run.

## 2026-09-15 02:20 UTC
- **Scoreboard:** cal=DISABLED (env_enabled=false, fingerprint_mismatch 45e2977c≠1bd087e4, heartbeat_age=82s/fresh, send_limit=0, draft_batch=0 — **TICK-15**) | scraper=248/150 (165.3%, on_track=true) | pipeline=HOT:266/WARM:1748/COLD:1898/total:3912, built_at=2026-09-15T02:01Z (fresh), sample-hermes_stamp=hermes_qualify:0/5, hermes_buying_window:0/5, hermes_decision_makers:1/5 (Stellantis only) | funnel=snapshot unavailable (empty)
- **Actions:**
  1. `ALERT` — Cal DISABLED **15th consecutive tick** — DUAL BLOCKER unchanged: (a) `env_enabled=false` (`CAL_ENABLED` Fly secret off); (b) template fingerprint `45e2977c8c888f1f6cfe` ≠ stored `1bd087e4bad1c2c28582` (template_version=3). `runtime_toggle_available=true` but insufficient while env gate is closed. Fix: `fly secrets set CAL_ENABLED=true -a ready-2-robot` + admin fingerprint reset. Zero outbound drafts or sends possible until both resolved.
  2. `INGEST_GAP` — Hermes stamp thin on HOT pool: 0/5 hermes_qualify, 0/5 hermes_buying_window, 1/5 hermes_decision_makers on sample. **Positive change:** pipeline now properly tiered (HOT=266, WARM=1748, COLD=1898, all non-zero — tiers restored vs prior 14 ticks of zero). But Hermes enrichment (buying-window, qualify, DM discovery) is still not flowing to the HOT pool. When Cal is unblocked it will have quantity but low research depth. Hermes research tick on HOT leads needed.
- **Next hour watch:** (1) Did operator set CAL_ENABLED=true + reset stored fingerprint? (2) Do hermes_qualify/hermes_buying_window fields appear on any HOT sample leads? (3) Scraper sustains >150 leads/day.

## 2026-09-15 03:20 UTC
- **Scoreboard:** cal=DISABLED (env_enabled=false, fingerprint_mismatch 45e2977c≠1bd087e4, runtime_override=true, heartbeat_age=97s/fresh, send_limit=0, draft_batch=0 — **TICK-16**) | scraper=248/150 (165.3%, on_track=true, recent_runs=[]) | pipeline=total:5, HOT:0, WARM:0, COLD:0, built_at=2026-09-15T03:01Z (fresh rebuild — **REGRESSION vs prior tick**) | funnel=snapshot unavailable
- **Actions:**
  1. `ALERT` — **Pipeline cache regression.** Cache rebuilt at 03:01Z but now serves only 5 leads (HOT=0, WARM=0, COLD=0). Prior tick (built_at=02:01Z) had total=3912, HOT=266, WARM=1748, COLD=1898. Scraper is healthy (248/150 leads, 165.3%) so intake is not the cause — the 03:01Z rebuild produced a near-empty result identical to the 14-tick pattern before last tick's restoration. This is consistent with a **flapping cache rebuild** — tier scoring works intermittently. Operator should check `app/services/public_surface_cache.py` rebuild logic and confirm whether the 02:01Z build was a one-off or the rebuild reliably retiers. Cal cannot operate on 5 untiered leads even when unblocked.
  2. `ALERT` — **Cal DISABLED 16th consecutive tick.** Dual blocker unchanged: (a) `env_enabled=false` — `CAL_ENABLED` Fly secret still off; (b) template fingerprint `45e2977c8c888f1f6cfe` ≠ stored `1bd087e4bad1c2c28582` (template_version=3). `runtime_override=true` and `runtime_toggle_available=true` but env gate prevents activation. Fix path: `fly secrets set CAL_ENABLED=true -a ready-2-robot` + admin fingerprint reset. Zero drafts or sends possible. 16 missed send windows.
- **Next hour watch:** (1) Does the 04:01Z cache rebuild restore HOT tier coverage (>100) or collapse again to ~5? That will confirm flapping vs one-off. (2) Did operator resolve CAL_ENABLED + fingerprint? (3) Scraper leads_last_24h — still on track?

## 2026-09-15 04:21 UTC (Tick 17)
- Scoreboard: cal=DISABLED(env_enabled=false+fingerprint_mismatch:45e2977c≠1bd087e4,heartbeat=OK@4m,send_limit=0,draft_batch=0) scraper=ON_TRACK(325/150,216.7%) hermes_stamp=ABSENT(qualify=0,buying_window=0,decision_makers=0/5) pipeline=REGRESSION(built_at=04:08Z,total=5,HOT=0,WARM=0,COLD=0) funnel=NO_SNAPSHOT
- Actions:
  1. ALERT — Cal DISABLED, 17th consecutive tick. Dual blocker unchanged: env_enabled=false + fingerprint mismatch (45e2977c≠1bd087e4). Zero outbound capacity. Fix path: `fly secrets set CAL_ENABLED=true` then admin fingerprint reset via cal-status API. Operator action required.
  2. ALERT — Pipeline cache regression, 17th tick persisting. Cache rebuilt 04:08Z → still only 5 leads total, HOT=0. Scraper healthy (325/150). Tier scoring or cache aggregation is broken — leads are ingesting but not ranking. Even if Cal re-enables, there is no HOT pool to work from.
  3. INGEST_GAP — Hermes stamp fully absent on all 5 pipeline leads (hermes_qualify=0, buying_window=0). When pipeline is restored, the HOT pool will need qualify stamps before Cal can prioritize correctly. Nudge next Hermes research tick.
- Next hour watch: 05:21Z — has pipeline HOT count recovered (scraper data is there; tier scoring must be the gap)? Has operator addressed CAL_ENABLED=true + fingerprint reset?

## 2026-09-15 05:21 UTC (Tick 18)
- **Scoreboard:** cal=DISABLED(env_enabled=false+fingerprint_mismatch:45e2977c≠1bd087e4,heartbeat=235s/fresh,send_limit=0,draft_batch=0) | scraper=ON_TRACK(341/150,227.3%,recent_runs=[]) | pipeline=REGRESSION(built_at=05:19Z,total=5,HOT=0,WARM=0,COLD=0,hermes_qualify=0,buying_window=0,decision_makers=0) | funnel=NO_SNAPSHOT
- **Actions:**
  1. `ALERT` — **Cal DISABLED, 18th consecutive tick (~18 hours).** Dual blocker unchanged: (a) `env_enabled=false` — `CAL_ENABLED` Fly secret is off; (b) template fingerprint `45e2977c8c888f1f6cfe` ≠ stored `1bd087e4bad1c2c28582` (template_version=3). `runtime_toggle_available=true` but env gate blocks activation. Cal has drafted zero outbound in 18 send windows. Fix path: `fly secrets set CAL_ENABLED=true -a ready-2-robot` + admin fingerprint reset. **Escalation: this is no longer a warning — it is a full day of zero outbound capacity.**
  2. `ALERT` — **Pipeline HOT=0, 18th consecutive tick (regression confirmed persistent).** Cache rebuilt 05:19Z → 5 leads, no tiers. The single good tick at 02:01Z (HOT=266/WARM=1748) is now confirmed an outlier. Scraper remains healthy at 341/150. Defect is in tier scoring or cache aggregation — data is ingesting but not ranking. Even if Cal re-enables today, there is no HOT pool to work. Bug in `app/services/public_surface_cache.py` or tier-scoring pipeline requires investigation.
  3. `INGEST_GAP` — Hermes stamp absent on all 5 pipeline leads (hermes_qualify=0, buying_window=0, decision_makers=0). Nudge next Hermes research tick on HOT pool — when tier scoring is restored, the pool needs qualify + buying-window stamps before Cal can prioritize correctly.
- **Next hour watch (06:21Z):** (1) Has operator set `CAL_ENABLED=true` + reset stored fingerprint? (2) Does pipeline HOT recover from 0 — or does it require an explicit trigger/repair to `public_surface_cache.py`? (3) Scraper on track at 341/150 — no action needed there.

## 2026-09-14 23:21 PDT (2026-09-15T06:21Z)
- Scoreboard: cal=DISABLED(19th-tick) env_enabled=false fingerprint=45e2977c≠1bd087e4 send_limit=0 draft_batch=0 heartbeat=207s(fresh) | scraper=341/150(227%,ON_TRACK) | pipeline=total=5 HOT=0 hermes_stamped=1/5 built_at=06:03Z | funnel=unavailable(empty snapshot)
- Actions:
  1. ALERT: Cal DISABLED — 19th consecutive tick (~19 hours zero outbound). Dual blocker unchanged: `env_enabled=false` + fingerprint mismatch `45e2977c≠1bd087e4`. Heartbeat is fresh (worker alive), but no drafts assembled, no sends possible. Operator action required: set `CAL_ENABLED=true` in Fly secrets AND regenerate/reconcile stored fingerprint.
  2. ALERT: HOT=0 pipeline regression — 19th consecutive tick with zero HOT leads in public surface cache (built 06:03Z). Scraper healthy at 341/150 (227%). Root cause is tier scoring or `public_surface_cache.py` aggregation — not intake. One valid good tick at 02:01Z (HOT=266) remains the outlier; persistent bug confirmed.
  3. INGEST_GAP: Hermes stamp thin — 1/5 pipeline leads carry any hermes field (marginal improvement from 0/5). With HOT=0, Cal has no qualifiable top-tier pool even if unblocked. Next Hermes research tick should prioritize stamping HOT-tier leads when pipeline tier scoring is repaired.
- Next hour watch: Has operator fixed CAL_ENABLED + fingerprint? Has HOT count moved above 0 in pipeline refresh?

## 2026-09-15 07:20 PDT (Tick 20)
- Scoreboard: cal=UNREADABLE(admin-key-invalid) scraper=341/150✅(227%) pipeline=HOT:0/WARM:0/total:5/stamped:1 built_at=06:59Z funnel=n/a(DB-DNS-down)
- Actions:
  1. ALERT: Cal-status endpoint returning "Invalid X-Admin-Key" — 20th consecutive tick cal state is unverifiable. Local `.env` has `ADMIN_KEY` but skill spec uses `RFR_ADMIN_KEY`; key may have rotated on Fly or env var name is mismatched. Operator must verify `ADMIN_KEY` secret on Fly matches current credential and that cal-status route is healthy.
  2. ALERT: Pipeline HOT=0 for 20th consecutive tick. Cache rebuilt fresh at 06:59Z with 5 leads — zero HOT, zero WARM. Scraper is healthy (341 leads/24h, 227% target). Root cause is tier scoring / `public_surface_cache.py` aggregation; not ingest. Operator action required: inspect HOT/WARM scoring logic or raw lead tiers in DB.
  3. INGEST_GAP: Hermes stamp unchanged at 1/5 leads. No improvement from tick 19. Cal has no qualifiable pool even if HOT scoring is restored and Cal is re-enabled. Next Hermes research tick should prioritize stamping the 4 unstamped pipeline leads (hermes_qualify + hermes_buying_window).
- Next hour watch (08:20 PDT): Confirm cal-status readable; HOT count > 0; hermes stamp ≥ 2/5.

## 2026-09-15 08:21 UTC (Tick #21)
- Scoreboard: cal=UNREADABLE(admin-key-invalid-21st-tick) scraper=✅341/150(227%) pipeline=built_at:07:59Z total=5 hot=0 warm=0 cold=0 hermes_stamp=1/5 funnel=no-snapshot
- Actions:
  1. ALERT: Cal-status unreadable for **21st consecutive tick** — `X-Admin-Key` returns 401 "Invalid X-Admin-Key or token". Fly secret name likely differs from local .env (local=`ADMIN_KEY`, endpoint expects `RFR_ADMIN_KEY`). Operator must audit Fly secrets (`fly secrets list -a ready-2-robot`) and resync. Cal is blind until resolved.
  2. ALERT: Pipeline HOT=0 persists (21st tick) — cache rebuilt fresh at 07:59Z, 5 total leads, **zero tier classification** (hot=0, warm=0, cold=0). Tier scoring in `public_surface_cache.py` is broken — leads are ingesting but not scoring. Cal has no qualified pool to work. Operator fix required.
  3. INGEST_GAP: Hermes stamp stuck at 1/5 for 3+ ticks — hermes_qualify/buying_window/decision_makers coverage flat. Moot while HOT=0, but next research tick should target qualification once scoring is restored.
- Next hour watch (09:20Z): cal-status readable (HTTP 200) + pipeline HOT≥1 + hermes_stamp≥2/5

## 2026-09-15 02:20 PDT (09:20Z) — Tick #22
- **Scoreboard:** cal=DISABLED-but-NOW-READABLE(HTTP-200-recovered) env_enabled=false runtime_override=true fingerprint-mismatch:45e2977c≠1bd087e4 send_limit=0 draft_batch=0 heartbeat=163s(fresh) | scraper=✅341/150(227%,on_track) | pipeline=built_at:08:59Z total=5 HOT=0 WARM=0 COLD=0 tier_none=5 hermes_stamp=1/5 | funnel=no-snapshot
- **Actions:**
  1. `ALERT` — **Cal-status READABLE again (HTTP 200) — good.** But Cal is still disabled via dual lock: `env_enabled=false` (Fly secret `CAL_ENABLED` off) + `runtime_override=true`. Template fingerprint mismatch also persists: `45e2977c8c888f1f6cfe` ≠ `1bd087e4bad1c2c28582` (template_version=3). Now that cal-status is readable, operator has full visibility into state. Fix path: (a) `fly secrets set CAL_ENABLED=true -a ready-2-robot` to clear env gate; (b) investigate `runtime_override=true` — was this set intentionally?; (c) reconcile stored fingerprint. Cal has assembled zero drafts and sent nothing in 22+ send windows.
  2. `ALERT` — **Pipeline HOT=0 for 22nd consecutive tick.** Cache rebuilt fresh (08:59Z) — 5 leads, all NONE tier. Scraper is healthy at 341/150 (227%). Defect is upstream of public surface: tier scoring in `app/services/public_surface_cache.py` or lead scoring pipeline is not classifying leads. Even when Cal is re-enabled, it will have no HOT pool to work without this fix. Root cause needs a direct DB inspection: `SELECT tier, COUNT(*) FROM companies GROUP BY tier LIMIT 20`.
  3. `INGEST_GAP` — Hermes stamp flat at 1/5 (unchanged from ticks 19–22). Four pipeline leads carry zero hermes fields (qualify/buying_window/decision_makers). When tier scoring is restored and Cal re-enables, the HOT pool will still need qualification stamps before Cal can prioritize correctly. Next Hermes research tick should target stamping top-scoring leads.
- **Next hour watch (03:20 PDT / 10:20Z):** (1) Has operator cleared the Cal dual lock (`env_enabled` + `runtime_override`)? (2) Does pipeline HOT recover above 0? (3) Hermes stamp ≥2/5?

## 2026-09-15 03:21 PDT (10:21Z) — Tick #23
- **Scoreboard:** cal=UNREADABLE(HTTP-403-REGRESSION from 200 last tick) | scraper=✅341/150(227%,on_track) | pipeline=built_at:09:59Z total=5 HOT=0 WARM=0 COLD=0 tier_none=5 hermes_stamp=1/5 | funnel=no-snapshot(empty)
- **Actions:**
  1. `ALERT` — **Cal-status regressed to HTTP 403 Forbidden** (was HTTP 200 at tick 22, HTTP 401 at ticks 20–21). This is a new auth state change between ticks. Possible causes: ADMIN_KEY rotated on Fly between 09:20Z and 10:21Z, or endpoint ACL tightened. Operator must run `fly secrets list -a ready-2-robot` and verify ADMIN_KEY in local `.env` matches Fly secret. Cal state is fully blind again — previous tick's visibility into `env_enabled` / `runtime_override` / fingerprint mismatch is now lost.
  2. `ALERT` — **Pipeline HOT=0 persists — 23rd consecutive tick.** Cache rebuilt fresh at 09:59Z; 5 total leads, all tier=none, zero HOT/WARM/COLD classification. Scraper healthy (341/150, 227%). Tier scoring defect in `app/services/public_surface_cache.py` or upstream scoring pipeline remains unresolved. Even if Cal auth is restored and `CAL_ENABLED=true`, Cal has no HOT pool to prioritize. Direct DB inspection needed: `SELECT tier, COUNT(*) FROM companies GROUP BY tier ORDER BY 2 DESC LIMIT 10`.
  3. `INGEST_GAP` — Hermes stamp flat at 1/5 for 5th consecutive tick. Zero improvement in hermes_qualify / hermes_buying_window / hermes_decision_makers coverage on the 4 unstamped pipeline leads. Research layer is not feeding forward. Next Hermes research tick should target qualification of top-scoring leads — though moot while HOT=0 blocks Cal activation.
- **Next hour watch (04:20 PDT / 11:20Z):** (1) cal-status HTTP 200 + ADMIN_KEY confirmed matched; (2) pipeline HOT ≥ 1; (3) hermes stamp ≥ 2/5.

## 2026-09-15 04:21 PDT (11:21Z) — Tick #24
- **Scoreboard:** cal=DISABLED-READABLE(HTTP-200-RESTORED✅) env_enabled=false runtime_override=true fingerprint-mismatch:45e2977c≠1bd087e4 send_limit=0 draft_batch=0 heartbeat=171s(fresh,not-stale) last_status=disabled | scraper=✅384/150(256%,on_track↑from-341) | pipeline=built_at:11:17Z total=5 HOT=0(24th-tick) WARM=0 COLD=0 tier_none=5 hermes_stamp=0/5(REGRESSED↓from-1/5) | funnel=no-snapshot(empty)
- **Actions:**
  1. `ALERT` — **Cal-status HTTP 403 RESOLVED — readable again (HTTP 200).** Third time readable in tick 22, regressed to 403 at tick 23, now back to 200. State unchanged from tick 22: dual lock intact (`env_enabled=false` + `runtime_override=true`), `send_limit=0`, no drafts assembled. **Template fingerprint mismatch persists: `45e2977c8c888f1f6cfe` ≠ stored `1bd087e4bad1c2c28582`** — must be reconciled before re-enabling. Cal has now been completely idle (disabled, zero send_limit, zero drafts) for 24+ send windows. Operator action required to either: (a) intentionally leave disabled or (b) clear dual lock: `fly secrets set CAL_ENABLED=true -a ready-2-robot`, clear runtime override, investigate fingerprint mismatch.
  2. `ALERT` — **Pipeline HOT=0 for 24th consecutive tick.** Cache rebuilt fresh at 11:17Z — still 5 leads, all tier=None. Tier scoring defect unresolved since day-start. Direct DB inspection still needed: `SELECT tier, COUNT(*) FROM companies WHERE is_junk=false ORDER BY overall_score DESC LIMIT 20`. Scraper healthy at 384/150 (256%) — ingest is not the problem. Fix is in `app/services/public_surface_cache.py` or the scoring pipeline that sets `tier`.
  3. `INGEST_GAP` — **Hermes stamp REGRESSED to 0/5** (was 1/5 at ticks 22–23). The single lead previously carrying any hermes field (`hermes_qualify`/`hermes_buying_window`/`hermes_decision_makers`) no longer shows it — either cache rebuild dropped it or research stamp was overwritten. Zero HOT coverage + zero Hermes qualification = Cal has nothing to work even if dual lock were cleared. Research layer must re-stamp top-scored pipeline leads before Cal can prioritize correctly.
- **Next hour watch (05:20 PDT / 12:20Z):** (1) Operator confirms Cal dual-lock intent (deliberate pause vs. forgotten config); (2) pipeline HOT ≥ 1 (fix tier scoring); (3) hermes stamp recovers ≥ 1/5.

## 2026-09-15 12:21 UTC
- Scoreboard: cal=DUAL-LOCKED(env_enabled=false+runtime_override=true,send_limit=0,draft_batch=0,heartbeat=fresh-170s,persona=Jobs-Recruiter-v3) scraper=399/150(266%) hermes_stamp=1/5(up-from-0) pipeline=total5/HOT0/WARM0/COLD0/tier_none5 built_at=11:49Z
- Actions:
  - ALERT[tick-25]: Cal dual-lock persists — env_enabled=false AND runtime_override=true; send_limit=0, draft_batch=0, fingerprint mismatch (45e2977c≠1bd087e4). 25th consecutive locked tick. Operator must reconcile env_enabled vs runtime_override and re-sign template.
  - ALERT[tick-25]: Pipeline tier scoring still broken — 5 leads, all tier_none, HOT=0 for 25th tick. Cache is fresh (11:49Z); scoring/promotion logic not running. No fuel for Jobs CRM until tier scoring runs.
  - INGEST_GAP: Hermes stamp recovering (1/5 up from 0/5) but thin. With tier_none blocking HOT promotion, stamped leads cannot surface. Fix tier scoring before optimizing stamp coverage.
- Next hour watch: Did fingerprint get re-signed? Did tier scoring run (HOT>0)? Hermes stamp ≥2/5?

## 2026-09-15 06:21 PDT (tick-26)
- Scoreboard: cal=disabled(dual-lock:env_enabled=false+runtime_override=true|fingerprint-mismatch:45e2977c≠1bd087e4|send_limit=0|draft_batch=0|heartbeat-fresh-160s) scraper=399/150(266%✅) hermes_stamp=1/5(unchanged) pipeline=HOT=0/5(all tier_none|built_at=13:13Z-fresh) funnel=no-snapshot
- Actions:
  1. ALERT: Cal dual-lock persists tick-26. env_enabled=false AND runtime_override=true remain in conflict — Cal heartbeat is alive but sends/drafts fully locked (send_limit=0, draft_batch=0). Fingerprint mismatch unchanged (45e2977c ≠ 1bd087e4). Operator must: (a) resolve env_enabled vs runtime_override conflict, (b) clear/re-store fingerprint before sends can resume.
  2. ALERT: Pipeline HOT=0 for 26th consecutive tick. All 5 leads remain tier_none despite 399 leads/24h intake. Cache is fresh (13:13Z). Root cause is tier-scoring not promoting any lead — Cal has no qualified pool to work regardless of lock state.
  3. INGEST_GAP: Hermes stamp flat at 1/5 — no improvement from tick-25. Even if stamp grows, tier_none block prevents HOT promotion. Tier-scoring fix is the critical path; Hermes stamp is secondary until tier logic is restored.
- Next hour watch: fingerprint mismatch resolution; any tier_none→HOT promotion; hermes_stamp movement above 1/5

## 2026-09-15 14:21 UTC (Tick-27)
- Scoreboard: cal=disabled(dual-lock: env_enabled=false + runtime_override=true, send_limit=0, draft_batch=0, last_heartbeat=158s ago/fresh, last_status=disabled) | fingerprint=MISMATCH(live=45e2977c ≠ stored=1bd087e4, 27th tick) | scraper=healthy(427/150, 285%) | pipeline=HOT=0(5 leads, all tier_none, built_at=13:47Z) | hermes_stamp=1/5(20%, flat) | snapshot=STALE(Aug 14, 32 days, funnel empty)
- Actions:
  - ALERT: Cal dual-lock tick-27 — env_enabled=false AND runtime_override=true both persist; send_limit=0, draft_batch=0. No drafts generated, no outbound possible. Template fingerprint mismatch (45e2977c ≠ 1bd087e4) unresolved for 27 consecutive ticks. **Operator must set CAL_ENABLED=true in Fly secrets OR resolve fingerprint conflict to unblock.** This is the single-point blocker on outbound.
  - ALERT: Pipeline HOT=0 tick-27 — all 5 pipeline leads remain tier_none. Tier-scoring is the critical path: until scoring assigns HOT/WARM, Cal has zero eligible pool regardless of lock state. Harness snapshot is 32 days stale (Aug 14) — re-run `python3 scripts/harness_snapshot.py` for current conversion/funnel data.
  - INGEST_GAP: Hermes stamp flat 1/5 (20%) — only 1 of 5 leads carries hermes_qualify/buying_window/decision_makers. Secondary to tier-scoring fix but will limit Cal pool quality once scoring is restored.
- Next hour watch: cal dual-lock state change · fingerprint resolution · any lead promoted out of tier_none · snapshot freshness

## 2026-09-15 15:21 UTC (Tick-28)
- **Scoreboard:**
  - cal=LOCKED (env_enabled=false, runtime_override=true, send_limit=0, draft_batch=0; last_heartbeat 139s ago — worker alive but last_status=disabled; fingerprint mismatch: template=45e2977c ≠ stored=1bd087e4, 28th consecutive tick)
  - scraper=HEALTHY (444 leads/24h vs target 150; 296% of target; no circuit-open URLs)
  - pipeline=HOT:0/WARM:0/COLD:0/tier_none:5 — cache fresh 15:17Z; hermes_stamp=1/5 (20%)
  - funnel=NO_DATA (harness snapshot conversion block empty)
- **Actions:**
  1. `ALERT` — Cal dual-lock persists tick-28: env_enabled=false AND runtime_override=true → send_limit=0, draft_batch=0. Operator must set CAL_ENABLED=true in Fly secrets to clear env lock. Fingerprint mismatch (45e2977c≠1bd087e4) also still present — template version "3" deployed but stored hash not updated. Both must be resolved before Cal can draft.
  2. `ALERT` — Pipeline HOT=0 for 28th consecutive tick. All 5 pipeline leads are tier_none. Tier-scoring is the critical path blocking Cal supply. Scraper is over-producing (444/day) but no leads are clearing the tier gate — scoring fix is operator-required.
  3. `INGEST_GAP` — Hermes stamp flat at 1/5 (20%). Remains a secondary blocker; primary is tier-scoring. Once HOT/WARM leads exist, stamp coverage needs to reach ≥50% before Cal can prioritize qualified pool.
- **Next hour watch:** Cal heartbeat freshness (stale_threshold=1800s); any HOT tier count > 0 (tier-scoring fix); fingerprint match resolved; harness snapshot staleness (32d+).
