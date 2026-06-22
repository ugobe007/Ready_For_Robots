# ReadyForRobots — Market Thesis

Living document for the agent harness **intelligence loop**. Updated by research missions (`MarketIntel`, `FrictionMiner`, `ProductThesis`). Execution missions must align with active bets unless fixing a P0 blocker (empty pipeline, broken deploy).

**Last updated:** 2026-06-23 (Phase 1 baseline — from quarantine sweeps, secondary-pass telemetry, UX direction)

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

Priority order matches north star: fix (1) before tuning (4). **Baseline below is evidence-backed** from the `friction-baseline` mission (2026-06-23), reconstructed from sweep reports in `reports/` (snapshot `intelligence` DB slice was unavailable — see theme 0).

**Reference sample:** `pipeline_junk_cleanup_20260619_222706.csv` — **3,163 junk rows**; `buyer_opportunity_junk_20260618_220744.csv` — 2,206 rows; `partnership_compound_quarantine_*` (2026-06-22) — 58 rows across 3 sweeps; `unknown_industry_keyword_analysis.txt` — 1,389 unknown-industry leads.

0. **Telemetry blind spot (meta-friction)** — snapshot `intelligence.junk_reasons`, `gap_frequency`, `industry_top` are all `available:false` because `database:null` (no `DATABASE_URL` in the snapshot run; sqlite template is skipped by `_db_session`). *The harness cannot self-measure friction — every baseline must be hand-reconstructed from ad-hoc CSVs.* Fix first or all other metrics stay un-trended.
1. **No buyer-intent signal (gate failures)** — **2,188 / 3,163 = 69%** of the junk sweep: `buyer opportunity gate: no buyer-intent signal found (labor, expansion, capex, RFP, deployment, or operations hiring)`. Company may be real but there is no actionable event. *Largest single friction by volume — newly the #1 theme.*
2. **RSS/HTML + market-report noise → Unknown industry** — **1,110 / 3,163 = 35%** of junk rows carry `Unknown` industry; the 1,389 unknown-industry leads are dominated by raw HTML boilerplate tokens (`nbsp`, `font`, `href`, `target`, `blank`, `color`, `6f6f6f`, `indexbox`) and market-research headline spam (`market analysis/forecast/size/trends`, `... to 2035`). Subsumes the old "headline junk" + "missing industry" themes.
3. **Robotics vendor / OEM contamination** — ~**167** rows flagged `robotics vendor / OEM` or `seller/vendor or publisher story`. Recurring offenders: Tesla (`Tesla moves`, `Tesla Semi`, `Tesla Stock`), Foxconn, SoftBank, Nvidia. Direct leak against the OEM-prospecting anti-bet.
4. **Headline fragments / verb-merge names in `companies.name`** — `Tesla moves`, `Lululemon claps`, `Olympic goalie shares`, `Havertys Furniture battles`, `Production demand`, `Multifamily`; plus mis-attributed fragments (`company name not found in signal text`, e.g. JLL) and one-off junk titles (`Ted Danson`, `Iran war`, `Hormuz`, `Cargo Thieves`). *Rep cannot act — no trust.*
5. **Partnership compounds** — **58** quarantined across three 2026-06-22 sweeps (rule shipped, still recurring). Two shapes: real vendor+entity (`Locus Robotics and GEODIS`, `Avery Dennison and TEXAID RFID`) and pure slogan noise (`Automation and AI Unlock New Value`, `Supercharge Your Retail and CPG AI Strategy`).
6. **Robot types too generic** — pipeline surface `robot_types: []` for all 9 visible leads; `robot_types_needed` not tied to deployment context. Limits outbound specificity. (Tune only after 0–5.)

**Harness metric:** once theme 0 is fixed, track junk-reason distribution, gap frequency, and industry_top in `reports/harness_snapshot_latest.json` → `intelligence` slice. Until then, cite the sweep CSVs above.

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

## Intelligence baseline (DB-backed, 2026-06-23)

First snapshot with live `intelligence` slice (`database.telemetry.status: connected`):

| Signal | Value | Implication |
|--------|-------|-------------|
| Unknown industry (with signals) | **960** | Rank 3 RSS/HTML + report filter still critical |
| Quarantined companies | **1,053** | Rectifier/quarantine working; volume worth trending |
| Pipeline gap scan (34 candidates) | `low_signals` 17, `industry` 11 | Surface leads thin on evidence + industry |
| Recent-name junk sample | 6% (OEM/vendor dominated) | Recent ingest cleaner than historical CSV sweeps |
| Pipeline surface | 9 leads, tiers unknown, empty robot_types | ProductSurface: tier + robot_types still broken on cache |

Historical CSV sweeps (pre-telemetry) remain directionally valid for **bulk junk** (69% no-intent) but should not be re-used once DB deltas are available.

---

## Ranked build backlog (agent-maintained)

Updated by research missions. Execution missions pull from here.

Re-ranked 2026-06-23 from friction baseline. Ranks now follow **volume × north-star order**: unblock measurement (theme 0), then attack the highest-volume name/event junk before copy/UX.

| Rank | Mission slug | Agent | Rationale (evidence) |
|------|--------------|-------|----------------------|
| ~~1~~ | ~~`snapshot-db-telemetry`~~ | PipelineHealth | ✅ **Done 2026-06-23** — `harness_env.py` + `database.telemetry`; intelligence slice live. |
| 1 | `buyer-intent-gate-triage` | LeadQuality | 69% of historical junk = "no buyer-intent signal". Suppress/route no-intent rows; instrument the gate. |
| 2 | `rss-html-strip-and-report-filter` | LeadQuality | **960 Unknown** industry rows with signals; HTML/market-report noise. |
| 3 | `vendor-oem-suppression-refresh` | LeadQuality | OEM blocklist gaps (~167 vendor leaks in sweeps; 6% in recent sample). |
| 4 | `partnership-quarantine-sweep` | LeadQuality | Recurring partnership-compound cleanup (58 in latest sweeps). |
| 5 | `industry-rescue-ontology` | LeadQuality | `industry` gap #2 on pipeline surface (11/34) once RSS noise removed. |
| 6 | `pipeline-action-copy` | ProductSurface | Industry-specific SIGNAL blurbs — only after names/events clean. |
| 7 | `next-actions-panel` | ProductSurface | Home right rail: top 3 autonomous actions (UX doc). |
| 8 | `humanoid-pilot-ranking` | LeadQuality + ProductSurface | Tag + rank humanoid pilot language. |

*`hospitality-headline-filter` folded into rank 3 (RSS/HTML strip covers hotel/geo header merges).*

---

## Review cadence

| Frequency | Action |
|-----------|--------|
| **Each mission** | Read snapshot `intelligence`; update backlog ranks if friction shifted |
| **Weekly** | `MarketIntel` mission — external scan → update Emerging + Puck sections |
| **Monthly** | Kill one bet, promote one from backlog |
| **Quarterly** | Puck review — still aligned with Detect→Advance? |

---

## Related docs

- [lead_quality_north_star.md](lead_quality_north_star.md)
- [readyforrobots-ux.md](readyforrobots-ux.md)
- [pipeline_process_and_scripts.md](pipeline_process_and_scripts.md)
- [AGENTS.md](../AGENTS.md)
