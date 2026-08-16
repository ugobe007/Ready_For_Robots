# Product simulation — Locus Origin search

**Date:** 2026-08-15  
**Input (assumed):** Locus Origin capability envelope (public)  
**Method:** Rank live RFR pipeline + logistics leads with Origin-oriented heuristics, then **manual filter** of junk names.  
**This is a simulation**, not a shipped ranking model.

---

## Capability envelope (Origin)

| Can | Cannot / weak |
|-----|----------------|
| Warehouse / fulfillment indoor | Outdoor ag, construction |
| Autonomous mobile nav with humans | Autonomous forklift heavy pallet racking (different machine) |
| Case/tote pick assist, GTP-style travel reduction | Floor scrubbing, welding, inspection crawl |
| Collaborative associate workflow | Lights-out fixed AS/RS replacement (Symbotic-class) |
| Chilled variants exist (HelloFresh public) | Deep freezer without hardware mods |

---

## Search UI mock

```
Robot: Locus Origin
Query: Where is this capability likely needed?

87 jobs found for Locus Origin     [simulation: 22 after manual quality gate]
```

### Results (click → deep Robot Job card)

| # | Where | Work hypothesis | Fit | Work | Timing | Buying | Why here (short) |
|---|-------|-----------------|-----|------|--------|--------|------------------|
| 1 | **Sysco** · foodservice DC network (pattern) | Case/tote pick travel · GTP-style | 90 | 96 | 80 | 60 | Automation pilots remit; food DC pick work; Hermes fit 87 |
| 2 | **Kenco** · Jeffersonville + network | Multi-client each-pick / replen travel | 90 | 96 | 80 | 60 | Proven Origin campus; labor/automation; expand/next site |
| 3 | **Lineage** · cold DCs | Cold case/unit movement (qualify payload) | 88 | 95 | 80 | 55 | Cold chain + labor; forklift vs AMR gate |
| 4 | **DHL Supply Chain** | Pick-assist / GTP in 3PL | 90 | 82 | 80 | 60 | Peer Locus deployments; Hermes fit |
| 5 | **Ryder** | 3PL fulfillment pick travel | 88 | 94 | 60 | 55 | Large 3PL; Hermes qualify |
| 6 | **XPO** | Distribution pick/replen | 88 | 81 | 80 | 55 | Network scale; automation narrative |
| 7 | **Medline** | Medical distribution pick | 85 | 81 | 80 | 55 | Hermes; cleanroom/temp qualify |
| 8 | **Dollar General** | DC / RDCs pick travel | 85 | 80 | 80 | 50 | Retail DC density |
| 9 | **FedEx Ground** | Hub/sort adjacent pick-assist (narrow) | 75 | 80 | 80 | 55 | Fit lower — sortation ≠ Origin core |
| 10 | **Radial** | E-comm fulfillment pick | 88 | 80 | 60 | 40 | Fulfillment native |
| 11 | **NFI Industries** | 3PL fulfillment | 85 | 80 | 60 | 40 | 3PL |
| 12 | **UPS SCS** | Contract logistics pick | 85 | 80 | 60 | 40 | Scale |
| 13 | **Burris Logistics** | Cold / food DC movement | 82 | 80 | 60 | 40 | Cold qualify |
| 14 | **RJW Logistics** | 3PL | 82 | 80 | 60 | 40 | |
| 15 | **Echo Global** | Broker-heavy — **audit flag** | 70 | 70 | 60 | 35 | May be asset-light; verify facilities |
| 16 | **Walmart** | Fulfillment/DC pick | 85 | 80 | 60 | 40 | Obvious; still real work |
| 17 | **Amazon** | Fulfillment — often incumbent-heavy | 70 | 65 | 60 | 40 | Non-obviousness low; competitive |
| 18 | **Home Depot** | DC/e-comm | 80 | 65 | 60 | 40 | |
| 19 | **Mondelez** | Plant/DC material flow | 75 | 80 | 60 | 40 | Plant vs DC qualify |
| 20 | **TFI International** | North America logistics | 78 | 80 | 60 | 40 | |
| 21 | **HelloFresh Phoenix** | Chilled induction→drop-off | 96 | 94 | 85 | 70 | Public Origin deploy; expansion EveryPlate |
| 22 | **PFG** (if in feed) | Foodservice DC pick | 88 | 85 | 70 | 50 | Peer to Sysco |

Raw heuristic dump (includes names later rejected): `origin_top100_candidates.json`.

---

## Brutal self-audit (this Origin list)

| Question | Rough call on top 22 |
|----------|----------------------|
| Work probably exists? | **~18/22** (Echo / some corp HQs weak) |
| Origin could plausibly perform? | **~16/22** (FedEx sort, Amazon incumbent, Lineage heavy pallet TBD) |
| Non-obvious? | **~8/22** (Sysco program, next Kenco site, Medline, Burris…) |
| Worth a salesperson investigating? | **~12/22** |

**Learning:** Live RFR data is still **company/lead shaped**. Many rows are logos, not facilities/workflows. Job discovery needs facility + work labeling or the SERP stays “hot logistics companies.”

That’s a product finding **without** a Locus meeting.

### Follow-on (Worksite branch)

Do **not** multiply robots (10×25) until WHERE is fixed. See `docs/product_sim/worksite/`.

Measured **Job Resolution Rate** on this same 22-row set (seed worksites only): run `python3 scripts/worksite_origin_baseline.py` → `worksite/origin_jrr_baseline.json`.

Target shape after Worksite layer:

> Sysco — Riverside DC · Case movement · Work: EVIDENCED · Origin fit: HIGH

not:

> Sysco — HOT — automation expansion

---

## Click-through (#1 deep card)

Reuse Sysco card from `docs/ceo_job_packs/locus_experiment/SHOW_B_three_jobs.md` — pattern-level, honest unknowns.
