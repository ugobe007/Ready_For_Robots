# Robot-Directed Discovery Scorecard — Origin lab

**Date:** 2026-08-16  
**Method:** Genuine web search (WebSearch), not RFR caches / ATS slug guessing  
**Robot:** Locus Origin–compatible work  
**Work units:** `pick_cases`, `replenish`, `move_totes`  
**Retrievals:** **7** targeted searches  

Company-directed LWY baseline: **~1** accepted LWO on Origin 18 (collector failure).

---

## Funnel

| Stage | Count |
|-------|------:|
| Retrieval operations | 7 |
| Candidate hits with WORK+COMPANY+LOCALITY signal | ~20 |
| **Accepted LWOs** (defensible) | **14** |
| Borderline / low-trust (spam career mirrors, weak locality) | 4 |
| Rejected for Origin fit (e.g. FedEx sortation-only) | 1+ |
| Strong Origin-shaped candidates (pick/replenish/tote in DC/FC) | **12** |

**RJDY = 14 / 7 × 100 ≈ 200 accepted LWOs per 100 retrievals**  
vs ATS slug path ≈ **2 per 100 requests** (1/53).

---

## Accepted Localized Work Observations (sample)

| # | Company | Locality | Work | Function | Evidence (short) | Conf. | Notes |
|---|---------|----------|------|----------|------------------|------:|-------|
| 1 | Kenco | Jeffersonville, IN | pick_cases | 3PL / FC | Warehouse Associate: pick/pack; may operate order picker | 0.90 | Was orphan WHAT-only in collectors |
| 2 | Sysco | Ocoee, FL (Central FL DC) | pick_cases | food DC | Official careers: Warehouse Order Selector — pick/palletize | 0.95 | Zero in company-directed pipeline |
| 3 | Dollar General | Atlanta, GA (Fresh DC) | pick_cases, replenish | food/retail DC | Order Selector: fill from pick slot; replenish pick areas | 0.88 | Collector zero |
| 4 | Dollar General | Ardmore, OK (Fresh DC) | pick_cases, replenish | perishable DC | Same selector language + locality | 0.88 | |
| 5 | Dollar General | Bethel, PA DC | pick_cases, replenish, move_totes | retail DC | Pick to rolling container/tote; replenish | 0.85 | |
| 6 | Dollar General | Blair / Missouri Valley, NE (DC) | pick_cases, replenish | retail DC | Order Selector opening for new DC | 0.80 | |
| 7 | Lineage | Fontana, CA | pick_cases | cold storage | Order Selector / case pick (LinkedIn ops history) | 0.70 | Historical; still LWO of work@place |
| 8 | Radial | Groningen, NL | move_totes | e-comm FC | Official case study: AMR tote/pallet transport to pick stations | 0.92 | Incumbent AMR — still proves work exists |
| 9 | HelloFresh | Irving, TX | fulfillment movement | meal-kit FC | Official story: Irving DC automation / induction–pick flow | 0.75 | AutoStore-heavy; tote travel partial |
| 10 | Home Depot | (network DCs; RDC/DFC types) | replenish | retail DC | Careers + ops language: replenishment / slotting in DCs | 0.65 | Locality weaker (type-level) |

*(Rows 3–6 counted as multiple LWOs where work units differ.)*

### Borderline (not counted in 14)

| Item | Why borderline |
|------|----------------|
| Amazon Arlington TX / Rogers AR “Order Picker” | Locality+work present but **drivecareer.us.com** mirrors look SEO/spam — verify on hiring.amazon.com before accepting |
| FedEx Package Handler | Locality often hub-level; work is sortation-load — **weak Origin fit** |

---

## Comparison

| Approach | Retrievals | Accepted LWOs | RJDY (/100 retrievals) |
|----------|----------:|--------------:|-----------------------:|
| ATS slug guessing (prior) | 53 | 1 | ~2 |
| Company-directed LWY collectors | many | ~1 | ~0 on zeros for mega-ops |
| **Robot-directed web search** | **7** | **14** | **~200** |

Qualitative: companies that were **impossible** for collectors (Sysco, Dollar General, Kenco place, Radial tote work) appear immediately when search starts from **work vocabulary**.

---

## Reading

1. Public localized physical-work evidence **exists** for Origin-shaped work.  
2. Our collector returning zeros was **pipeline failure**.  
3. Starting from the robot’s compatible work is a higher-yield discovery path than reconstructing every company’s footprint first.  
4. Footprint remains valuable as **enrichment/verification**, not the only on-ramp.

---

## Do not / do

| Stop | Start |
|------|--------|
| More company-directed LWY Python runs | Robot-directed search loops (work vocab → LWO) |
| ATS slug spam | Ranked retrieval for WORK+COMPANY+LOCALITY |
| Mapping all Worksites before any job | Assemble Robot Jobs from observations; enrich map as byproduct |

---

## Superseded by v2

Keep this scorecard as **v1** (known-universe evidence availability).

Next: **open-world** discovery — [ROBOT_DIRECTED_DISCOVERY_V2.md](./ROBOT_DIRECTED_DISCOVERY_V2.md) · [origin_open_world_pilot.md](./origin_open_world_pilot.md).

Do not treat 200/100 as a durable KPI; redefine funnel as queries → documents inspected → LWOs → jobs.
