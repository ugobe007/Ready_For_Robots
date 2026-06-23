# ReadyForRobots — Market Thesis

Living document for the agent harness **intelligence loop**. Updated by research missions (`MarketIntel`, `FrictionMiner`, `ProductThesis`). Execution missions must align with active bets unless fixing a P0 blocker (empty pipeline, broken deploy).

**Last updated:** 2026-06-23 (harness re-rank + ingest OEM PR gate + prod cache refresh)

---

## What we sell

**Time-to-first-meeting on verified robot buyer intent** — not raw news, not vendor PR, not headline scrapes dressed as companies.

Product shape (from `docs/readyforrobots-ux.md`):

**Detect → Qualify → Engage → Advance**

Users want deals moving forward without doing the work. The control surface is autonomy + next actions, not another dashboard.

---

## Buyer segments we serve today

| Segment | Signal in ingest | Friction observed |
|---------|------------------|-------------------|
| **Warehouse / logistics** | DC automation, AMR pilots, labor shortages | Strong intent; partnership headlines (`X and Y`) pollute buyer rows |
| **Food retail / CPG** | Store automation, picking, back-of-house | Headline fragments (`Food Lion's`, geo stubs) |
| **Hospitality** | Housekeeping labor, hotel ops | Many geo/hotel headline merges; low actionable density |
| **Healthcare / life sciences** | Cardinal-style distribution, lab automation | Better names when rectification passes |
| **Airport / municipal** | Pittsburgh Airport-style infra projects | Good buyer shape when name is clean |

**Rule:** Optimize segment copy and ranking only after **names/events** are clean for that segment.

---

## Emerging segments (weak signals — watch, do not over-build)

| Segment | Leading indicator | Puck direction |
|---------|-------------------|----------------|
| **Humanoid pilots** | Earnings + trade press; catalog/benchmark assets we already maintain | Readiness scoring + spec language before RFP |
| **Last-mile / micro-fulfillment** | Grocery + Ocado-style partnerships vs buyer ops | Split partnership PR from operator buyers |
| **Regional EU / APAC operators** | Non-US company names with automation capex language | Industry rescue failures suggest ontology gap |

---

## Friction themes (internal — from secondary pass & quarantine)

Priority order matches north star: fix (1) before tuning (4). **Baseline below is now live-DB-backed** from the `friction-baseline` mission (2026-06-23). The live `intelligence` slice was restored this mission (see theme 0); historical CSV sweeps are retained for bulk-junk shape.

**Reference sample:** live snapshot `intelligence` slice (`database.telemetry: connected`, sample 400); `pipeline_junk_cleanup_20260619_222706.csv` — **3,163 junk rows**; `partnership_compound_quarantine_*` (2026-06-22) — **58** rows across 3 sweeps (30/14/14); `unknown_industry_keyword_analysis.txt` — 1,389 unknown-industry leads.

0. **Telemetry blind spot (meta-friction) — ✅ RESOLVED 2026-06-23.** The live snapshot had silently regressed: `.venv-harness` was missing `sqlalchemy`/`psycopg2-binary` (→ `database.telemetry: unavailable`), then `requests` (→ `junk_reasons` blocked), then `fastapi` (→ `gap_frequency` blocked). Despite a real Postgres `DATABASE_URL` in `.env`, all three intelligence sub-slices read `available:false`. Fixed by installing the four deps into the harness venv and pinning them in **`harness/requirements.txt`** so the slice doesn't silently degrade again. *Lesson: a "Done" telemetry mission can regress at the venv layer with no code change — pin deps, don't assume.*
1. **No buyer-intent signal (gate failures)** — **2,188 / 3,163 = 69%** of the historical junk sweep: `buyer opportunity gate: no buyer-intent signal found (labor, expansion, capex, RFP, deployment, or operations hiring)`. Company may be real but there is no actionable event. *Largest single friction by volume in the historical backlog.*
2. **RSS/HTML + market-report noise → Unknown industry** — **960** live Unknown-industry companies with signals (the #1 industry bucket by far; next is Logistics 385). In the CSV sweep, **1,110 / 3,163 = 35%** of junk rows carry `Unknown`; the 1,389 unknown-industry leads are dominated by raw HTML boilerplate tokens (`nbsp` 3,557, `font` 3,343, `href`, `target`, `blank`, `color`, `6f6f6f`, `indexbox`) and market-research headline spam (`market analysis/forecast/size/trends`, `... to 2035`/`2034`).
3. **Robotics vendor / OEM contamination — now the dominant *recent-flow* leak.** The live junk sample (400 recent companies, **5.8% junk rate**) is **100% vendor/OEM**: `robotics vendor / OEM (not a buyer opportunity)` 17 + `name pattern matches automation/robotics vendor` 6 = 23/23. Historical sweep adds 99 `seller/vendor or publisher story` + 68 `robotics vendor / OEM`. Recurring offenders: Tesla, Foxconn, SoftBank, Nvidia. Direct leak against the OEM-prospecting anti-bet — *and the single thing still entering the pipeline.*
4. **Headline fragments / verb-merge / mis-attributed names in `companies.name`** — `invalid_name` bucket = **80** rows in the sweep; mis-attributed fragments (`company name not found in signal text`, e.g. JLL) = 8. Examples: `Tesla moves`, `Lululemon claps`, `Havertys Furniture battles`, `Production demand`, one-off junk titles (`Ted Danson`, `Iran war`). *Rep cannot act — no trust.*
5. **Partnership compounds** — **58** quarantined across three 2026-06-22 sweeps (rule shipped, still recurring). Two shapes: real vendor+entity (`Serve Robotics and White Castle`, `Locus Robotics and GEODIS`) and pure slogan noise (`Shaping Biotech And Life Sciences`, `Flying Taxis And Self-Driving Trucks`).
6. **Robot types too generic / pipeline surface empty** — live pipeline feed is **empty** (`cache_pending: true`, surface `lead_count: 0`, `robot_types: []`); gap scan shows `low_signals` 17 + `industry` 11 dominate the 34 candidates with gaps. Limits outbound specificity. (Tune only after 0–5.)

**Harness metric:** theme 0 is fixed — track junk-reason distribution, gap frequency, and industry_top live in `reports/harness_snapshot_latest.json` → `intelligence` slice each mission. Re-install via `python3 -m pip install -r harness/requirements.txt` if the slice degrades.

---

## 12-month puck (bets)

Active bets the Orchestrator should prefer when choosing build missions:

| # | Bet | Why now | Success signal |
|---|-----|---------|----------------|
| 1 | **Clean buyer identity layer** | Everything downstream is wasted on headline junk | ↓ junk reasons in snapshot; ↑ pipeline rows passing rectification |
| 2 | **Live actionable surface** | Hero ticker + pipeline prove "real leads exist" | Rep can name company + robot type in <60s from home |
| 3 | **Autonomous next actions** | UX north star is Advance, not browse | Activate CTR, time-to-first-outreach (when instrumented) |
| 4 | **Vertical-aware copy** | Hospitality vs warehouse pain differs | Tier blurbs match industry; A/B on SIGNAL activation |
| 5 | **Humanoid readiness lane** | Category inflection; we have catalog asset | Distinct ranking/copy for humanoid pilot language |

---

## Anti-bets (explicitly not chasing)

- Becoming a general **robotics news aggregator** (no differentiation vs RSS)
- **OEM/vendor prospecting** as default buyer pipeline (mode=`buyer` filter exists for a reason)
- **Volume over quality** — more pipeline rows while `built_at` fresh but names broken
- **Dashboard parity** with Salesforce/HubSpot — we win on intent + autonomy

---

## Intelligence baseline (live-DB-backed, 2026-06-23)

Live `intelligence` slice (`database.telemetry.status: connected`) — restored this mission after a silent venv regression (theme 0). All sub-slices now `available:true`:

| Signal | Value | Implication |
|--------|-------|-------------|
| Recent junk sample (400) | **5.8%** junk, **100% vendor/OEM** (17 + 6) | Marginal *fresh* ingest leak is now OEM/vendor, not no-intent → rank 3 matters for live flow |
| Industry distribution (top) | **Unknown 960**, Logistics 385, Hospitality 258, Healthcare 257, Auto&Mfg 244, Food Svc 199, Airports 172, Retail 147 | Unknown dwarfs every real vertical → RSS/HTML + report filter is the biggest classifiable win |
| Pipeline gap scan (34 candidates) | `low_signals` 17, `industry` 11, `crm_descriptors` 5 | Surface leads thin on evidence + industry |
| API summary | 3,881 leads (306 hot / 1,639 warm / 1,936 cold); 4,258 companies; 11,841 signals | Scale of corpus the gates run against |
| Pipeline surface | **empty** (`cache_pending`, lead_count 0, robot_types []) | PipelineHealth: feed not built; surface metrics unmeasurable until cache refreshes |

Historical CSV sweeps remain directionally valid for **bulk backlog junk** (69% no-intent, 35% Unknown). The live slice supersedes them for *recent-flow* trends — note the divergence: bulk backlog is no-intent-dominated, recent ingest is vendor/OEM-dominated.

---

## Ranked build backlog (agent-maintained)

Updated by research missions. Execution missions pull from here.

Re-ranked 2026-06-23 from friction baseline. Ranks now follow **volume × north-star order**: unblock measurement (theme 0), then attack the highest-volume name/event junk before copy/UX.

| Rank | Mission slug | Agent | Rationale (evidence) |
|------|--------------|-------|----------------------|
| ~~–~~ | ~~`snapshot-db-telemetry`~~ | PipelineHealth | ✅ **Done 2026-06-23**, then **re-fixed 2026-06-23** (friction-baseline): venv lost `sqlalchemy`/`requests`/`fastapi` → slice silently degraded. Deps now pinned in `harness/requirements.txt`. |
| ~~1~~ | ~~`vendor-oem-suppression-refresh`~~ | LeadQuality | ✅ **Done 2026-06-23** — blocklist + catalog buyer denylist; **28** active OEM rows quarantined. |
| ~~1~~ | ~~`rss-html-strip-and-report-filter`~~ | LeadQuality | ✅ **Done 2026-06-23** — stripped **1,714** RSS HTML signals; quarantined **704** Unknown junk rows (865→153 live). |
| ~~1~~ | ~~`partnership-quarantine-sweep`~~ | LeadQuality | ✅ **Done 2026-06-23** — re-sweep found **0** new compounds (58 quarantined 2026-06-22). |
| ~~2~~ | ~~`industry-rescue-ontology`~~ | LeadQuality | ✅ **Done 2026-06-23** — **62** industries applied, **39** stubs quarantined; Unknown **153→52**. |
| ~~1~~ | ~~`pipeline-cache-refresh-health`~~ | PipelineHealth | ✅ **Done 2026-06-23** — full cache rebuild; **35** durable feed leads, **9** anonymous visible; `cache_pending` idle. |
| ~~1~~ | ~~`pipeline-action-copy`~~ | ProductSurface | ✅ **Done 2026-06-23** — industry `pipeline_action` + `share_blurb` on cards; cache rebuilt (**35** feed). |
| ~~1~~ | ~~`next-actions-panel`~~ | ProductSurface | ✅ **Done 2026-06-23** — home hero + pipeline right rail; `GET /api/leads/pipeline-next-actions`. |
| ~~1~~ | ~~`humanoid-pilot-ranking`~~ | LeadQuality + ProductSurface | ✅ **Done 2026-06-23** — `humanoid_pilot_*` tiers on cards; humanoid leads boost next-actions + pipeline badge. |
| ~~1~~ | ~~`unknown-industry-residual-sweep`~~ | LeadQuality | ✅ **Done 2026-06-23** — **8** industries applied, **48** quarantined; active Unknown w/ signals **56→0**. |
| ~~1~~ | ~~`hero-live-pipeline-panel`~~ | ProductSurface | ✅ **Done 2026-06-23** — Supabase-like hero panel (superseded by on-brand redesign). |
| ~~1~~ | ~~`hero-pipeline-on-brand`~~ | ProductSurface | ✅ **Done 2026-06-23** — compact editorial Live pipeline widget; 360px column, site purple/teal theme. |
| ~~1~~ | ~~`pipeline-robot-types-surface`~~ | PipelineHealth | ✅ **Done 2026-06-23** — `robot_types_needed` on slim pipeline cards; **35/35** feed rows. |
| ~~1~~ | ~~`vendor-oem-live-flow`~~ | LeadQuality | ✅ **Done 2026-06-23** — broad OEM quarantine; **19** pattern/blocklist rows hidden. |
| ~~2~~ | ~~`contact-gap-backfill`~~ | LeadQuality | ✅ **Done 2026-06-23** — `--require-gap contact`; batch filled **3** contacts (Apollo key still needed for scale). |
| ~~1~~ | ~~`ingest-oem-pr-gate`~~ | LeadQuality | ✅ **Done 2026-06-23** — `_buyer_opportunity_gate` on article context at ingest. |
| ~~2~~ | ~~`apollo-contact-hot-warm`~~ | LeadQuality | ✅ **Done 2026-06-23** — `--priority-tier HOT/WARM`; Apollo key present but **403** on free plan search API. |
| ~~2~~ | ~~`crm-descriptors-backfill`~~ | LeadQuality | ✅ **Done 2026-06-23** — robot-fit fallback in CRM extractor; **4** fills; gap **30→28**. |

### Conversion funnel (browse → signup) — standing ProductSurface directive

See [conversion_agent_challenges.md](conversion_agent_challenges.md). Agents must tighten CTA continuity, post-auth landing, and upgrade moments every mission.

| Rank | Mission slug | Agent | Rationale |
|------|--------------|-------|-----------|
| ~~1~~ | ~~`conversion-funnel-pass`~~ | ProductSurface | ✅ **Done 2026-06-23** — Pricing→signup, default `/pipeline`, dual home CTA, save-limit upgrade toast. |
| ~~1~~ | ~~`entitlement-honesty`~~ | ProductSurface | ✅ **Done 2026-06-23** — Free/Pro/Premium pricing; `/me` entitlements; profile meters. |
| ~~2~~ | ~~`pipeline-research-upsell`~~ | ProductSurface | ✅ **Done 2026-06-23** — blurred research teaser + Pro CTA for free users. |
| 1 | `profile-usage-meters` | ProductSurface | ✅ folded into entitlement-honesty |
| ~~2~~ | ~~`mobile-signup-cta`~~ | ProductSurface | ✅ **Done 2026-06-23** — mobile header pill + drawer workspace CTA. |

*Next: periodic prod cache refresh after deploys. Headline HOT/WARM quarantine + Hunter named-email upgrade pass shipped 2026-06-23.*

*Re-ranked 2026-06-23 (friction-baseline): vendor/OEM promoted to #1 because the live slice shows it is the dominant recent-flow leak, whereas no-intent (69%) is a historical-backlog cleanup. `hospitality-headline-filter` folded into rank 2 (RSS/HTML strip covers hotel/geo header merges). `pipeline-cache-refresh-health` added — feed is empty.*

---

## Review cadence

| Frequency | Action |
|-----------|--------|
| **Each mission** | Read snapshot `intelligence`; update backlog ranks if friction shifted; **ProductSurface:** tighten conversion (CTA continuity, proof density, friction on signup path) |
| **Weekly** | `MarketIntel` mission — external scan → update Emerging + Puck sections |
| **Monthly** | Kill one bet, promote one from backlog |
| **Quarterly** | Puck review — still aligned with Detect→Advance? |

---

## Related docs

- [lead_quality_north_star.md](lead_quality_north_star.md)
- [readyforrobots-ux.md](readyforrobots-ux.md)
- [pipeline_process_and_scripts.md](pipeline_process_and_scripts.md)
- [AGENTS.md](../AGENTS.md)
