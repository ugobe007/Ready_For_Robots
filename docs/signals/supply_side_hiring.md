# Supply-Side Hiring Intelligence

**Category**: Market context only — **not a buyer source**

This document tracks hiring activity at **robot makers** (supply side). This information provides market context about which robot companies are scaling, but it **never creates buyer opportunities** and **never defines the product or market thesis**.

## Critical Distinction

- ✅ **Buyer-side hiring**: A *potential buyer* (hospital, warehouse, manufacturer) hiring robotics/automation roles → **readiness signal** attached to that company's robot job opportunity
- ❌ **Supply-side hiring**: A *robot maker* hiring engineers/operators → **market context only** (helps understand which vendors are active, not who's buying)

**Example**:
- Hospital hiring "Robotic Surgery Coordinator" ✅ → signal on hospital's robot job opportunity
- Intuitive Surgical hiring "Robotics Engineer" ❌ → market context only, not a buyer signal

---

## Grace Gong Physical AI Hiring List (Week 98, 2026-10-11)

**Source:** Grace Gong "On My Radar" — 36 physical AI companies actively hiring, ranked by % headcount growth (past 90 days).

**What this tells us**: Which robot makers are scaling through hiring. This indicates:
- Product development velocity (hiring engineers → new capabilities)
- Category maturity (humanoid concentration, foundation model platforms)
- Geographic clusters (Bay Area, Beijing, Shenzhen)
- Market readiness (industrial/applied vs research-stage)

**What this does NOT tell us**: Who is buying robots. These companies are **supply**, not demand.

### Key Observations

| Metric | Value | Market Context |
|--------|-------|----------------|
| **Humanoid concentration** | 25% (9 companies) | Category inflection — humanoid makers are hiring |
| **Foundation model platforms** | 22% (8 companies) | AI-first robotics is active investment area |
| **China presence** | 25% (9 companies: 5 Beijing, 4 Shenzhen) | Global supply competition |
| **Bay Area cluster** | 25% (9 companies) | Dense VC/talent ecosystem |
| **Industrial/applied** | 11% (4 companies) | Smaller cohort focused on near-term deployments |

### Notable Companies by Category

**Foundation Models (AI platforms)**:
- **Physical Intelligence** (San Francisco) — foundation models for robots
- **Skild AI** (Pittsburgh) — one brain to control many kinds of robots
- **XDOF** (San Mateo) — foundation models for robots

**Humanoid Platform**:
- **Figure** (Sunnyvale) — general-purpose humanoid robot
- **Apptronik** (Austin) — modular humanoid robots
- **LimX Dynamics** (Shenzhen) — full-size general-purpose humanoids

**Industrial/Applied**:
- **Path Robotics** (Columbus) — AI welding robots
- **Maven Robotics** (Santa Clara) — autonomous industrial robots
- **Standard Bots** (Glen Cove) — AI-native industrial robots

### Use Cases for This Intelligence

**Valid**:
- ✅ Understand which robot categories are attracting investment (humanoids, foundation models)
- ✅ Track which vendors are scaling (may affect supply availability, pricing)
- ✅ Identify emerging players to add to robot classification index
- ✅ Geographic market context (where supply clusters are forming)

**Invalid**:
- ❌ Treat robot maker hiring as a buyer signal
- ❌ Add these companies to buyer pipeline
- ❌ Scrape these companies' career pages looking for robot jobs (they're not buyers)
- ❌ Use this list to define ICP or market thesis

---

## Data Sources

- **Grace Gong LinkedIn**: Weekly "On My Radar" lists
- **Robot maker career pages**: Engineering/operations hiring trends (supply-side only)

## Scripts

- `scripts/ingest_grace_gong_hiring_list.py` — Ingests Grace Gong weekly lists
- `app/services/grace_gong_career_pages.py` — Career page scraping config
- `scripts/verify_supply_demand_distinction.py` — Verification that supply-side data doesn't leak into buyer pipeline

**Critical**: These scripts **must never** add robot makers to the buyer pipeline or scrape rotation as opportunities. They are market context only.

---

## Related Documents

- [HUMAN_JOB_LISTINGS_AUDIT_V2.md](../../HUMAN_JOB_LISTINGS_AUDIT_V2.md) — Buyer-side vs supply-side hiring distinction
- [CLAUDE.md](../../CLAUDE.md) — Product definition and signal taxonomy
- [docs/robot_opportunity_sources.csv](../robot_opportunity_sources.csv) — Buyer-side hiring signals (separate)
