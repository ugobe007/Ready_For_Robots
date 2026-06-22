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

Priority order matches north star: fix (1) before tuning (4).

1. **Headline junk in `companies.name`** — RSS merges, geo stubs (`Upstate NY`, `Co Antrim`), truncated headlines (`US Sets`, `'We want`). *Rep cannot act — no trust.*
2. **Partnership compounds** — `Serve Robotics and White Castle` is not a buyer; White Castle row may be. Rule shipped; periodic sweeps needed.
3. **Rectification failures** — contact/CRM filled but entity coherence fails → quarantine. *Data looks rich but record is still junk.*
4. **Missing industry** — `industry_rescue` failed on otherwise HOT rows. Blocks vertical copy and rep triage.
5. **Low signals** — pipeline-visible but thin evidence. Rank inflation risk.
6. **Robot types too generic** — `robot_types_needed` present but not tied to deployment context. Limits outbound specificity.

**Harness metric:** track gap frequency and junk reason distribution in `reports/harness_snapshot_latest.json` → `intelligence` slice.

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

## Ranked build backlog (agent-maintained)

Updated by research missions. Execution missions pull from here.

| Rank | Mission slug | Agent | Rationale |
|------|--------------|-------|-----------|
| 1 | `friction-baseline` | FrictionMiner | Establish thesis + gap/junk telemetry baseline (research) |
| 2 | `partnership-quarantine-sweep` | LeadQuality | Recurring partnership compound cleanup |
| 3 | `industry-rescue-ontology` | LeadQuality | Reduce `industry_rescue` failures on HOT rows |
| 4 | `hospitality-headline-filter` | LeadQuality | Cut hotel/geo headline merges at ingest |
| 5 | `pipeline-action-copy` | ProductSurface | Industry-specific SIGNAL blurbs on pipeline cards |
| 6 | `next-actions-panel` | ProductSurface | Home right rail: top 3 autonomous actions (UX doc) |
| 7 | `humanoid-pilot-ranking` | LeadQuality + ProductSurface | Tag + rank humanoid pilot language |

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
